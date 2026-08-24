"""Read-only inventory for processed documents and chunk coverage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

Classification = Literal["covered", "intentional", "duplicate", "failed", "stale", "missing", "unknown"]
_REQUIRED_CHUNK_METADATA = frozenset({"document", "source", "role", "section"})


@dataclass(frozen=True)
class DocumentCoverage:
    document_id: str
    metadata_path: str
    source_path: str
    classification: Classification
    chunk_file: str | None
    chunk_count: int
    duplicate_of: str | None = None


@dataclass(frozen=True)
class InventoryReport:
    summary: dict[str, int]
    documents: list[DocumentCoverage]
    malformed_chunk_files: list[str]
    chunk_files_without_metadata: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "documents": [asdict(document) for document in self.documents],
            "malformed_chunk_files": self.malformed_chunk_files,
            "chunk_files_without_metadata": self.chunk_files_without_metadata,
        }


def _relative_stem(path: Path, root: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix().casefold()


def _classification_for_uncovered(metadata: dict[str, Any], duplicate_of: str | None) -> Classification:
    if duplicate_of:
        return "duplicate"
    status = str(metadata.get("processing_status", "")).casefold()
    if status == "failed" or metadata.get("processing_errors"):
        return "failed"
    if status in {"excluded", "intentional", "skipped"}:
        return "intentional"
    if status == "stale":
        return "stale"
    if status == "missing":
        return "missing"
    return "unknown"


def inventory_processed_documents(processed_dir: str | Path) -> InventoryReport:
    processed_root = Path(processed_dir)
    metadata_root = processed_root / "metadata"
    chunks_root = processed_root / "chunks"

    metadata_files = sorted(metadata_root.rglob("*.json"))
    chunk_files = sorted(chunks_root.rglob("*.json"))

    chunk_by_stem: dict[str, tuple[Path, list[dict[str, Any]]]] = {}
    malformed_files: list[str] = []
    total_chunks = 0
    empty_chunks = 0
    incomplete_chunks = 0

    for chunk_path in chunk_files:
        try:
            payload = json.loads(chunk_path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("chunk payload must be a list")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            malformed_files.append(chunk_path.relative_to(processed_root).as_posix())
            continue

        chunks = [item for item in payload if isinstance(item, dict)]
        chunk_by_stem[_relative_stem(chunk_path, chunks_root)] = (chunk_path, chunks)
        total_chunks += len(chunks)
        for chunk in chunks:
            if not str(chunk.get("content", "")).strip():
                empty_chunks += 1
            metadata = chunk.get("metadata")
            if (
                not isinstance(metadata, dict)
                or not _REQUIRED_CHUNK_METADATA.issubset(metadata)
                or any(not metadata.get(key) for key in _REQUIRED_CHUNK_METADATA)
            ):
                incomplete_chunks += 1

    metadata_records: list[tuple[Path, dict[str, Any]]] = []
    hash_to_document_ids: dict[str, list[str]] = {}
    for metadata_path in metadata_files:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        metadata_records.append((metadata_path, metadata))
        file_hash = str(metadata.get("file_hash", "")).strip()
        document_id = str(metadata.get("document_id") or metadata_path.stem)
        if file_hash:
            hash_to_document_ids.setdefault(file_hash, []).append(document_id)

    documents: list[DocumentCoverage] = []
    covered_documents = 0
    for metadata_path, metadata in metadata_records:
        document_id = str(metadata.get("document_id") or metadata_path.stem)
        source_path = str(metadata.get("source_path") or metadata.get("source_file") or "")
        stem = _relative_stem(metadata_path, metadata_root)
        chunk_entry = chunk_by_stem.get(stem)
        duplicate_of = None
        file_hash = str(metadata.get("file_hash", "")).strip()
        same_hash_ids = hash_to_document_ids.get(file_hash, []) if file_hash else []
        if not chunk_entry and len(same_hash_ids) > 1:
            covered_same_hash = [
                candidate
                for candidate in same_hash_ids
                if any(item.document_id == candidate and item.classification == "covered" for item in documents)
            ]
            if covered_same_hash:
                duplicate_of = covered_same_hash[0]
            else:
                duplicate_of = next((candidate for candidate in same_hash_ids if candidate != document_id), None)

        if chunk_entry:
            chunk_path, chunks = chunk_entry
            classification: Classification = "covered"
            covered_documents += 1
            chunk_file = chunk_path.relative_to(processed_root).as_posix()
            chunk_count = len(chunks)
        else:
            classification = _classification_for_uncovered(metadata, duplicate_of)
            chunk_file = None
            chunk_count = 0

        documents.append(
            DocumentCoverage(
                document_id=document_id,
                metadata_path=metadata_path.relative_to(processed_root).as_posix(),
                source_path=source_path,
                classification=classification,
                chunk_file=chunk_file,
                chunk_count=chunk_count,
                duplicate_of=duplicate_of,
            )
        )

    documents.sort(key=lambda item: (item.document_id.casefold(), item.metadata_path.casefold()))
    metadata_stems = {_relative_stem(path, metadata_root) for path in metadata_files}
    chunk_files_without_metadata = sorted(
        path.relative_to(processed_root).as_posix()
        for stem, (path, _) in chunk_by_stem.items()
        if stem not in metadata_stems
    )
    summary = {
        "metadata_files": len(metadata_files),
        "chunk_files": len(chunk_files),
        "chunk_files_without_metadata": len(chunk_files_without_metadata),
        "chunks": total_chunks,
        "covered_documents": covered_documents,
        "unchunked_documents": len(metadata_files) - covered_documents,
        "malformed_chunk_files": len(malformed_files),
        "empty_chunks": empty_chunks,
        "chunks_missing_required_metadata": incomplete_chunks,
    }
    return InventoryReport(
        summary=summary,
        documents=documents,
        malformed_chunk_files=sorted(malformed_files),
        chunk_files_without_metadata=chunk_files_without_metadata,
    )
