"""Validate processed chunks and build deterministic import records."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.db.models import DocumentChunk

IssueCode = Literal[
    "malformed_file",
    "invalid_chunk",
    "empty_content",
    "missing_provenance",
    "duplicate_id",
    "duplicate_hash",
]

_ROLE_NORMALIZATION = {
    "accountant": "accounting",
    "accounting": "accounting",
    "ketoan": "accounting",
    "sale": "sales",
    "sales": "sales",
    "technician": "technician",
    "ktv": "technician",
    "manager": "owner",
    "owner": "owner",
    "general": "general",
}
_SCOPE_BY_ROLE = {
    "accounting": ["accounting", "general"],
    "sales": ["sales", "general"],
    "technician": ["technician", "general"],
    "owner": ["accounting", "sales", "technician", "owner", "general"],
    "general": ["general"],
}


@dataclass(frozen=True)
class ImportRecord:
    id: str
    document_id: str
    source_id: str
    content: str
    role: str
    access_scope: list[str]
    section: str
    source_path: str
    content_type: str
    metadata: dict[str, Any]
    embedding_model: str
    embedding_version: str
    pipeline_version: str
    chunk_version: str
    content_hash: str


@dataclass(frozen=True)
class ImportIssue:
    code: IssueCode
    file: str
    chunk_id: str | None
    detail: str


class InvalidEmbeddingError(ValueError):
    """Raised when an embedding batch violates the BGE-M3 storage contract."""


@dataclass(frozen=True)
class EmbeddedRecord:
    record: ImportRecord
    embedding: list[float]


@dataclass(frozen=True)
class DryRunResult:
    summary: dict[str, int]
    records: list[ImportRecord]
    issues: list[ImportIssue]

    def to_dict(self, *, include_records: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "summary": self.summary,
            "issues": [asdict(issue) for issue in self.issues],
        }
        if include_records:
            payload["records"] = [asdict(record) for record in self.records]
        return payload


def prepare_embedding_batches(
    records: Iterable[ImportRecord],
    *,
    embedder: Any,
    batch_size: int = 16,
    expected_dimensions: int = 1024,
    normalization_tolerance: float = 1e-3,
) -> Iterator[list[EmbeddedRecord]]:
    """Embed records in stable, bounded batches without writing to a database."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    ordered = sorted(records, key=lambda record: record.id)
    for start in range(0, len(ordered), batch_size):
        batch = ordered[start : start + batch_size]
        vectors: Sequence[Sequence[float]] = embedder.embed_documents(
            [record.content for record in batch],
            batch_size=batch_size,
        )
        if len(vectors) != len(batch):
            raise InvalidEmbeddingError(f"embedder returned {len(vectors)} vectors for {len(batch)} records")

        embedded_batch: list[EmbeddedRecord] = []
        for record, vector in zip(batch, vectors, strict=True):
            values = [float(value) for value in vector]
            if len(values) != expected_dimensions:
                raise InvalidEmbeddingError(
                    f"chunk {record.id} expected {expected_dimensions} dimensions, got {len(values)}"
                )
            norm = math.sqrt(sum(value * value for value in values))
            if not math.isfinite(norm) or abs(norm - 1.0) > normalization_tolerance:
                raise InvalidEmbeddingError(f"chunk {record.id} embedding is not normalized")
            embedded_batch.append(EmbeddedRecord(record=record, embedding=values))
        yield embedded_batch


def upsert_embedded_batch(session: Session, batch: Sequence[EmbeddedRecord]) -> dict[str, int]:
    """Transactionally upsert one validated embedding batch."""
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    if not batch:
        return counts

    ids = [item.record.id for item in batch]
    try:
        existing_rows = (
            session.execute(
                select(
                    DocumentChunk.id,
                    DocumentChunk.content_hash,
                    DocumentChunk.document_id,
                    DocumentChunk.source_id,
                    DocumentChunk.role,
                    DocumentChunk.access_scope,
                    DocumentChunk.section,
                    DocumentChunk.source_path,
                    DocumentChunk.content_type,
                    DocumentChunk.chunk_metadata.label("metadata"),
                    DocumentChunk.embedding_model,
                    DocumentChunk.embedding_version,
                    DocumentChunk.pipeline_version,
                    DocumentChunk.chunk_version,
                ).where(DocumentChunk.id.in_(ids))
            )
            .mappings()
            .all()
        )
        existing = {row["id"]: row for row in existing_rows}

        changed: list[EmbeddedRecord] = []
        for item in batch:
            current = existing.get(item.record.id)
            if current is None:
                counts["inserted"] += 1
                changed.append(item)
            elif all(
                current[key] == value
                for key, value in {
                    "content_hash": item.record.content_hash,
                    "document_id": item.record.document_id,
                    "source_id": item.record.source_id,
                    "role": item.record.role,
                    "access_scope": item.record.access_scope,
                    "section": item.record.section,
                    "source_path": item.record.source_path,
                    "content_type": item.record.content_type,
                    "metadata": item.record.metadata,
                    "embedding_model": item.record.embedding_model,
                    "embedding_version": item.record.embedding_version,
                    "pipeline_version": item.record.pipeline_version,
                    "chunk_version": item.record.chunk_version,
                }.items()
            ):
                counts["unchanged"] += 1
            else:
                counts["updated"] += 1
                changed.append(item)

        if not changed:
            return counts

        values = [
            {
                "id": item.record.id,
                "document_id": item.record.document_id,
                "source_id": item.record.source_id,
                "content": item.record.content,
                "embedding": item.embedding,
                "role": item.record.role,
                "access_scope": item.record.access_scope,
                "section": item.record.section,
                "source_path": item.record.source_path,
                "content_type": item.record.content_type,
                "metadata": item.record.metadata,
                "embedding_model": item.record.embedding_model,
                "embedding_version": item.record.embedding_version,
                "pipeline_version": item.record.pipeline_version,
                "chunk_version": item.record.chunk_version,
                "content_hash": item.record.content_hash,
            }
            for item in changed
        ]
        statement = insert(DocumentChunk.__table__).values(values)
        update_columns = {
            column.name: getattr(statement.excluded, column.name)
            for column in DocumentChunk.__table__.columns
            if column.name not in {"id", "created_at"}
        }
        session.execute(
            statement.on_conflict_do_update(index_elements=[DocumentChunk.__table__.c.id], set_=update_columns)
        )
        session.commit()
        return counts
    except Exception:
        session.rollback()
        raise


def embed_and_upsert_records(
    records: Iterable[ImportRecord],
    *,
    embedder: Any,
    session_factory: Callable[[], Session],
    batch_size: int = 16,
) -> dict[str, int]:
    """Embed and upsert all records in independently committed batches."""
    totals = {"inserted": 0, "updated": 0, "unchanged": 0, "batches": 0}
    batches = prepare_embedding_batches(records, embedder=embedder, batch_size=batch_size)
    for batch in batches:
        session = session_factory()
        try:
            counts = upsert_embedded_batch(session, batch)
        finally:
            session.close()
        for key in ("inserted", "updated", "unchanged"):
            totals[key] += counts[key]
        totals["batches"] += 1
    return totals


def _document_id(chunk_id: str) -> str:
    match = re.match(r"^(.+?)_chunk_\d+(?:_v\d+)?$", chunk_id, flags=re.IGNORECASE)
    return match.group(1) if match else chunk_id


def _normalized_role(value: Any) -> str:
    raw = str(value or "general").strip().casefold()
    return _ROLE_NORMALIZATION.get(raw, raw)


def _access_scope(role: str, metadata: dict[str, Any]) -> list[str]:
    explicit = metadata.get("access_scope")
    if isinstance(explicit, list) and explicit:
        normalized = [_normalized_role(item) for item in explicit]
        if role not in normalized:
            normalized.insert(0, role)
        if role != "general" and "general" not in normalized:
            normalized.append("general")
        return list(dict.fromkeys(normalized))
    return list(_SCOPE_BY_ROLE.get(role, [role, "general"]))


def _make_record(
    chunk: dict[str, Any],
    *,
    embedding_model: str,
    embedding_version: str,
    pipeline_version: str,
    chunk_version: str,
) -> ImportRecord:
    chunk_id = str(chunk["chunk_id"]).strip()
    content = unicodedata.normalize("NFC", str(chunk["content"]).strip())
    metadata = chunk["metadata"]
    source = unicodedata.normalize("NFC", str(metadata["source"]).strip()).replace("\\", "/")
    role = _normalized_role(metadata["role"])
    canonical_hash_input = f"{source}\n{content}".encode()
    content_hash = hashlib.sha256(canonical_hash_input).hexdigest()

    clean_metadata = json.loads(json.dumps(metadata, ensure_ascii=False))
    return ImportRecord(
        id=chunk_id,
        document_id=_document_id(chunk_id),
        source_id=source,
        content=content,
        role=role,
        access_scope=_access_scope(role, metadata),
        section=unicodedata.normalize("NFC", str(metadata["section"]).strip()),
        source_path=source,
        content_type=str(metadata.get("content_type") or "document").strip().casefold(),
        metadata=clean_metadata,
        embedding_model=embedding_model,
        embedding_version=embedding_version,
        pipeline_version=pipeline_version,
        chunk_version=chunk_version,
        content_hash=content_hash,
    )


def dry_run_import(
    chunks_dir: str | Path,
    *,
    embedding_model: str = "BAAI/bge-m3",
    embedding_version: str = "1",
    pipeline_version: str = "1",
    chunk_version: str = "1",
) -> DryRunResult:
    chunks_root = Path(chunks_dir)
    files = sorted(chunks_root.rglob("*.json"))
    records: list[ImportRecord] = []
    issues: list[ImportIssue] = []
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    total_chunks = 0
    invalid = 0
    duplicates = 0

    for path in files:
        relative_path = path.relative_to(chunks_root).as_posix()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("chunk payload must be a list")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            issues.append(ImportIssue("malformed_file", relative_path, None, type(error).__name__))
            invalid += 1
            continue

        total_chunks += len(payload)
        for position, chunk in enumerate(payload):
            if not isinstance(chunk, dict):
                issues.append(ImportIssue("invalid_chunk", relative_path, None, f"position={position}"))
                invalid += 1
                continue

            chunk_id = str(chunk.get("chunk_id") or "").strip() or None
            content = str(chunk.get("content") or "").strip()
            if not content:
                issues.append(ImportIssue("empty_content", relative_path, chunk_id, f"position={position}"))
                invalid += 1
                continue

            metadata = chunk.get("metadata")
            required = ("document", "source", "role", "section")
            if not chunk_id or not isinstance(metadata, dict) or any(not metadata.get(key) for key in required):
                issues.append(ImportIssue("missing_provenance", relative_path, chunk_id, f"position={position}"))
                invalid += 1
                continue

            record = _make_record(
                chunk,
                embedding_model=embedding_model,
                embedding_version=embedding_version,
                pipeline_version=pipeline_version,
                chunk_version=chunk_version,
            )
            if record.id in seen_ids:
                issues.append(ImportIssue("duplicate_id", relative_path, record.id, "duplicate stable chunk id"))
                duplicates += 1
                continue
            seen_ids.add(record.id)
            if record.content_hash in seen_hashes:
                issues.append(ImportIssue("duplicate_hash", relative_path, record.id, "duplicate source/content hash"))
                duplicates += 1
                continue
            seen_hashes.add(record.content_hash)
            records.append(record)

    records.sort(key=lambda record: record.id)
    summary = {
        "files": len(files),
        "chunks": total_chunks,
        "valid": len(records),
        "invalid": invalid,
        "duplicates": duplicates,
    }
    return DryRunResult(summary=summary, records=records, issues=issues)
