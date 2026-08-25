"""Durable R2 reconciliation and worker orchestration."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import DocStatus, DocumentRegistry, IngestionJobRecord, IngestionRun, IngestionRunStatus
from src.services.s3_document_service import S3DocumentService

logger = logging.getLogger(__name__)


class IngestionRunConflict(RuntimeError):
    """Raised when an administrator starts a second simultaneous run."""


class DurableIngestionService:
    def __init__(self, *, document_service: S3DocumentService | None = None) -> None:
        self.document_service = document_service or S3DocumentService()

    @staticmethod
    def _active_run(db: Session) -> IngestionRun | None:
        return (
            db.query(IngestionRun)
            .filter(IngestionRun.status.in_([IngestionRunStatus.queued, IngestionRunStatus.running]))
            .order_by(IngestionRun.created_at.desc())
            .first()
        )

    def start_run(self, db: Session, *, created_by: str | None = None, dry_run: bool = False) -> dict:
        if self._active_run(db):
            raise IngestionRunConflict("an ingestion run is already in progress")
        run = IngestionRun(
            id=str(uuid.uuid4()),
            status=IngestionRunStatus.queued,
            dry_run=dry_run,
            created_by=created_by,
        )
        db.add(run)
        db.commit()
        try:
            reconciliation = self.document_service.sync_registry(db)
            pending = db.query(DocumentRegistry).filter(DocumentRegistry.status == DocStatus.pending).all()
            run.total_documents = len(pending)
            run.skipped_documents = reconciliation.get("skipped", 0)
            if dry_run:
                run.status = IngestionRunStatus.dry_run
                run.completed_at = datetime.now(UTC)
            else:
                for doc in pending:
                    db.add(IngestionJobRecord(run_id=run.id, document_id=doc.id, status=DocStatus.pending))
                run.status = IngestionRunStatus.running
                run.started_at = datetime.now(UTC)
                if not pending:
                    run.status = IngestionRunStatus.completed
                    run.completed_at = datetime.now(UTC)
            db.commit()
            return self.serialize_run(run, reconciliation=reconciliation)
        except Exception as error:
            db.rollback()
            run.status = IngestionRunStatus.failed
            run.error_message = str(error)[:1000]
            run.completed_at = datetime.now(UTC)
            db.add(run)
            db.commit()
            raise

    def serialize_run(self, run: IngestionRun, *, reconciliation: dict | None = None) -> dict:
        return {
            "run_id": run.id,
            "status": run.status.value,
            "dry_run": run.dry_run,
            "total_documents": run.total_documents,
            "processed_documents": run.processed_documents,
            "failed_documents": run.failed_documents,
            "skipped_documents": run.skipped_documents,
            "current_document": run.current_document,
            "error_message": run.error_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "reconciliation": reconciliation,
        }

    def latest_status(self, db: Session) -> dict:
        run = db.query(IngestionRun).order_by(IngestionRun.created_at.desc()).first()
        if run is None:
            return {"status": "no_active_run", "run_id": None}
        payload = self.serialize_run(run)
        failures = (
            db.query(IngestionJobRecord, DocumentRegistry)
            .join(DocumentRegistry, IngestionJobRecord.document_id == DocumentRegistry.id)
            .filter(IngestionJobRecord.run_id == run.id, IngestionJobRecord.status == DocStatus.failed)
            .all()
        )
        payload["failures"] = [
            {"document_id": doc.id, "s3_key": doc.s3_key, "error_message": job.error_message or doc.error_message}
            for job, doc in failures
        ]
        return payload

    def list_documents(self, db: Session, *, status: str | None = None, limit: int = 100) -> list[dict]:
        query = db.query(DocumentRegistry)
        if status:
            try:
                query = query.filter(DocumentRegistry.status == DocStatus(status))
            except ValueError as error:
                raise ValueError(f"invalid document status: {status}") from error
        query = query.order_by(DocumentRegistry.created_at.desc()).limit(min(limit, 500))
        return [
            {
                "id": doc.id,
                "s3_key": doc.s3_key,
                "filename": doc.filename,
                "category": doc.category,
                "role": doc.role,
                "file_size": doc.file_size,
                "content_hash": doc.content_hash,
                "status": doc.status.value,
                "error_message": doc.error_message,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
            }
            for doc in query.all()
        ]

    def retry_failed(self, db: Session, *, created_by: str | None = None, document_ids: list[int] | None = None) -> dict:
        if self._active_run(db):
            raise IngestionRunConflict("an ingestion run is already in progress")
        query = db.query(DocumentRegistry).filter(DocumentRegistry.status == DocStatus.failed)
        if document_ids:
            query = query.filter(DocumentRegistry.id.in_(document_ids))
        failed = query.all()
        for doc in failed:
            doc.status = DocStatus.pending
            doc.error_message = None
        db.commit()
        if not failed:
            return {"run_id": None, "requeued": 0, "status": "no_failed_documents"}
        run = IngestionRun(id=str(uuid.uuid4()), status=IngestionRunStatus.running, created_by=created_by, started_at=datetime.now(UTC), total_documents=len(failed))
        db.add(run)
        db.flush()
        for doc in failed:
            db.add(IngestionJobRecord(run_id=run.id, document_id=doc.id, status=DocStatus.pending))
        db.commit()
        return {"run_id": run.id, "requeued": len(failed), "status": run.status.value}

    def process_one_batch(self, db: Session, *, run_id: str | None = None, limit: int = 1) -> int:
        """Claim and process at most ``limit`` jobs; safe to call from a Railway worker loop."""
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first() if run_id else self._active_run(db)
        if run is None or run.status not in (IngestionRunStatus.queued, IngestionRunStatus.running):
            return 0
        run.status = IngestionRunStatus.running
        stale_before = datetime.now(UTC) - timedelta(minutes=30)
        db.query(IngestionJobRecord).filter(
            IngestionJobRecord.run_id == run.id,
            IngestionJobRecord.status == DocStatus.processing,
            IngestionJobRecord.claimed_at < stale_before,
        ).update({"status": DocStatus.pending, "claimed_at": None}, synchronize_session=False)
        db.commit()
        processed = 0
        for _ in range(max(1, limit)):
            job = (
                db.query(IngestionJobRecord)
                .filter(IngestionJobRecord.run_id == run.id, IngestionJobRecord.status == DocStatus.pending)
                .order_by(IngestionJobRecord.id)
                .first()
            )
            if job is None:
                break
            job.status = DocStatus.processing
            job.claimed_at = datetime.now(UTC)
            job.attempts += 1
            doc = db.query(DocumentRegistry).filter(DocumentRegistry.id == job.document_id).first()
            db.commit()
            if doc is None:
                job.status = DocStatus.failed
                job.error_message = "document registry row not found"
                run.failed_documents += 1
            else:
                run.current_document = doc.s3_key
                try:
                    self.document_service.process_document(db, doc)
                    job.status = DocStatus.processed
                    job.completed_at = datetime.now(UTC)
                    run.processed_documents += 1
                    processed += 1
                except Exception as error:
                    job.status = DocStatus.failed
                    job.error_message = str(error)[:1000]
                    run.failed_documents += 1
                    logger.exception("Ingestion job failed for %s", doc.s3_key)
            db.commit()
        remaining = db.query(func.count(IngestionJobRecord.id)).filter(
            IngestionJobRecord.run_id == run.id,
            IngestionJobRecord.status.in_([DocStatus.pending, DocStatus.processing]),
        ).scalar() or 0
        if remaining == 0:
            run.status = IngestionRunStatus.completed
            run.current_document = None
            run.completed_at = datetime.now(UTC)
            db.commit()
        return processed


durable_ingestion = DurableIngestionService()
