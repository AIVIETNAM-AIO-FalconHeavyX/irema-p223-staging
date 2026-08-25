"""Cloudflare R2 reconciliation and durable document processing service."""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
import unicodedata
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from src.cloud.s3_service import s3_service
from src.config import get_settings
from src.db.models import DocStatus, DocumentRegistry

logger = logging.getLogger(__name__)
_SUPPORTED_EXTS = {".pdf", ".docx", ".pptx", ".xlsx", ".mp4", ".webm", ".md", ".txt"}
_s3_ready = False


def is_s3_ready() -> bool:
    return _s3_ready


def set_s3_ready(status: bool) -> None:
    global _s3_ready
    _s3_ready = status


def _safe_unlink(file_path: Path) -> None:
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        logger.debug("Could not remove temporary path %s", file_path, exc_info=True)


class S3DocumentService:
    """R2 is the source of truth; PostgreSQL stores processed searchable chunks."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.role_mapping = self.settings.role_mapping
        self._embedder = None

    def sync_registry(self, db: Session) -> dict[str, int]:
        """Reconcile R2 keys and ETags into the idempotent registry."""
        stats = {"new": 0, "updated": 0, "unchanged": 0, "skipped": 0}
        objects = self._list_s3_objects()
        for obj in objects:
            s3_key = unicodedata.normalize("NFC", str(obj["Key"]).replace("\\", "/"))
            filename = s3_key.rsplit("/", 1)[-1]
            ext = Path(filename).suffix.lower()
            if ext not in _SUPPORTED_EXTS:
                stats["skipped"] += 1
                continue
            parts = s3_key.split("/")
            category = parts[0] if len(parts) > 1 else "General_doc"
            role = self.role_mapping.get(category, "general")
            etag = str(obj.get("ETag", "")).strip('"')
            content_hash = f"s3:{etag}:{obj.get('Size', 0)}"
            existing = db.query(DocumentRegistry).filter(DocumentRegistry.s3_key == s3_key).first()
            if existing is None:
                db.add(
                    DocumentRegistry(
                        s3_key=s3_key,
                        filename=filename,
                        category=category,
                        role=role,
                        file_size=int(obj.get("Size", 0) or 0),
                        content_hash=content_hash,
                        status=DocStatus.pending,
                    )
                )
                stats["new"] += 1
            elif existing.content_hash == content_hash:
                stats["unchanged"] += 1
            else:
                existing.filename = filename
                existing.category = category
                existing.role = role
                existing.file_size = int(obj.get("Size", 0) or 0)
                existing.content_hash = content_hash
                existing.status = DocStatus.pending
                existing.error_message = None
                existing.processed_at = None
                stats["updated"] += 1
        db.commit()
        return stats

    def process_pending(self, db: Session) -> dict[str, int]:
        stats = {"processed": 0, "failed": 0}
        pending = db.query(DocumentRegistry).filter(DocumentRegistry.status == DocStatus.pending).all()
        for doc in pending:
            try:
                self.process_document(db, doc)
                stats["processed"] += 1
            except Exception:
                stats["failed"] += 1
                logger.exception("R2 document failed: %s", doc.s3_key)
        return stats

    def process_document(self, db: Session, doc: DocumentRegistry) -> dict:
        """Process one source and atomically replace its active chunk set."""
        from src.db import SessionLocal
        from src.migration.chunk_importer import records_from_chunk_payload, replace_document_records
        from src.preprocess.markdown_pipeline import MarkdownProcessingPipeline
        from src.preprocess.pipeline import PreprocessingPipeline

        doc.status = DocStatus.processing
        doc.error_message = None
        db.commit()
        local_path: Path | None = None
        staged_path: Path | None = None
        try:
            local_path = self.fetch_to_temp(doc.s3_key)
            pipeline = PreprocessingPipeline()
            safe_parts = [p for p in doc.s3_key.split("/") if p not in ("", ".", "..")]
            staged_path = pipeline.raw_dir.joinpath(*safe_parts)
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, staged_path)
            suffix = staged_path.suffix.lower()

            if suffix in {".md", ".txt"}:
                raw_text = staged_path.read_text(encoding="utf-8", errors="replace")
                if suffix == ".txt" or not raw_text.lstrip().startswith("---"):
                    raw_text = (
                        "---\n"
                        f"document_id: {doc.id}\n"
                        f"title: {doc.filename}\n"
                        f"role: {doc.role}\n"
                        f"source_path: {doc.s3_key}\n"
                        "---\n\n"
                        + raw_text
                    )
                md_path = pipeline.markdown_dir.joinpath(*safe_parts).with_suffix(".md")
                md_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.write_text(raw_text, encoding="utf-8")
            else:
                result = pipeline.process_file(staged_path)
                if result is None:
                    raise ValueError(f"unsupported or empty source: {doc.s3_key}")
                md_path, _, _ = result

            markdown_result = MarkdownProcessingPipeline().process_markdown_file(md_path)
            if markdown_result is None:
                raise ValueError(f"markdown processing failed: {doc.s3_key}")
            _, chunks_path = markdown_result
            payload = json.loads(chunks_path.read_text(encoding="utf-8"))
            records = records_from_chunk_payload(payload)
            if not records:
                raise ValueError(f"no valid chunks generated: {doc.s3_key}")
            records = [replace(record, document_id=str(doc.id)) for record in records]
            if self._embedder is None:
                from src.embedding.embedder import EmbeddingService

                self._embedder = EmbeddingService()
            counts = replace_document_records(
                records,
                embedder=self._embedder,
                session_factory=SessionLocal,
                batch_size=16,
            )
            doc.status = DocStatus.processed
            doc.processed_at = datetime.now(UTC)
            doc.error_message = None
            db.commit()
            return {"chunks": len(records), **counts}
        except Exception as error:
            db.rollback()
            doc.status = DocStatus.failed
            doc.error_message = str(error)[:1000]
            db.add(doc)
            db.commit()
            raise
        finally:
            if staged_path:
                _safe_unlink(staged_path)
            if local_path:
                _safe_unlink(local_path)

    def retry_failed_documents(self, db: Session, doc_ids: list[int] | None = None) -> int:
        query = db.query(DocumentRegistry).filter(DocumentRegistry.status == DocStatus.failed)
        if doc_ids:
            query = query.filter(DocumentRegistry.id.in_(doc_ids))
        failed_docs = query.all()
        for doc in failed_docs:
            doc.status = DocStatus.pending
            doc.error_message = None
        db.commit()
        return len(failed_docs)

    def fetch_to_temp(self, s3_key: str) -> Path:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(s3_key).suffix, prefix="r2doc_") as tmp:
            tmp_path = Path(tmp.name)
        s3_service.s3_client.download_file(s3_service.bucket_name, s3_key, str(tmp_path))
        return tmp_path

    def _list_s3_objects(self) -> list[dict]:
        objects: list[dict] = []
        paginator = s3_service.s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=s3_service.bucket_name):
            objects.extend(page.get("Contents", []))
        return objects
