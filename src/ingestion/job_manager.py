from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from threading import Lock
from typing import Any

from src.ingestion.pii_scanner import PIIScanResult
from src.ingestion.security_scanner import SecurityScanResult

logger = logging.getLogger(__name__)


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    EXTRACTING = "EXTRACTING"
    SCANNING = "SCANNING"
    PENDING_REVIEW = "PENDING_REVIEW"  # Waiting for human approval
    APPROVED = "APPROVED"  # Human approved all issues
    CHUNKING = "CHUNKING"
    INDEXING = "INDEXING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class IssueDecision:
    """Human decision on a single security or PII issue."""

    issue_index: int  # Index in the issues list
    approved: bool  # True = keep file/ignore issue; False = reject
    reviewer_note: str = ""  # Optional note from reviewer


@dataclass
class IngestionJob:
    """Represents the full lifecycle of one document ingestion job."""

    job_id: str
    file_name: str
    file_size_bytes: int
    uploaded_by: str
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Processing results
    file_hash: str = ""
    temp_file_path: str = ""  # Path to temp file on disk (cleaned up on DONE/CANCEL)
    extracted_text_preview: str = ""  # First 500 chars of extracted text (for preview)
    chunks_count: int = 0
    indexed_count: int = 0

    # Scan results
    security_scan: SecurityScanResult | None = None
    pii_scan: PIIScanResult | None = None

    # HITL
    issue_decisions: list[IssueDecision] = field(default_factory=list)
    hitl_required: bool = False
    hitl_resolved: bool = False

    # Metadata output
    output_markdown_path: str = ""
    output_metadata_path: str = ""

    # Error tracking
    error_message: str = ""
    processing_log: list[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        ts = datetime.utcnow().strftime("%H:%M:%S")
        self.processing_log.append(f"[{ts}] {message}")
        logger.info(f"[Job {self.job_id[:8]}] {message}")

    def set_status(self, status: JobStatus) -> None:
        self.status = status
        self.updated_at = datetime.utcnow()
        self.log(f"Status → {status.value}")

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a dict safe for JSON serialization (for API responses)."""
        return {
            "job_id": self.job_id,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "uploaded_by": self.uploaded_by,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "file_hash": self.file_hash,
            "chunks_count": self.chunks_count,
            "indexed_count": self.indexed_count,
            "hitl_required": self.hitl_required,
            "hitl_resolved": self.hitl_resolved,
            "error_message": self.error_message,
        }

    def to_preview_dict(self) -> dict[str, Any]:
        """Return detailed preview for HITL review."""
        security_issues = []
        if self.security_scan:
            for idx, issue in enumerate(self.security_scan.issues):
                security_issues.append(
                    {
                        "index": idx,
                        "type": "SECURITY",
                        "issue_type": issue.issue_type,
                        "severity": issue.severity,
                        "location": issue.location,
                        "text_snippet": issue.text_snippet,
                        "confidence": issue.confidence,
                        "requires_hitl": issue.requires_hitl,
                        "auto_rejected": issue.auto_rejected,
                    }
                )

        pii_issues = []
        if self.pii_scan:
            for idx, loc in enumerate(self.pii_scan.hitl_locations):
                pii_issues.append(
                    {
                        "index": idx,
                        "type": "PII",
                        "entity_type": loc.entity_type,
                        "masked_value": loc.masked_value,
                        "section_title": loc.section_title,
                        "section_index": loc.section_index,
                        "char_start": loc.char_start,
                        "char_end": loc.char_end,
                        "context_before": loc.context_before,
                        "context_after": loc.context_after,
                        "confidence": loc.confidence,
                        "note": (
                            "Low confidence detection — please verify this is actually PII before confirming removal."
                        ),
                    }
                )

        return {
            **self.to_summary_dict(),
            "extracted_text_preview": self.extracted_text_preview,
            "security_issues": security_issues,
            "pii_hitl_issues": pii_issues,
            "processing_log": self.processing_log[-20:],  # Last 20 log entries
        }


class IngestionJobManager:
    """
    In-memory job store for managing ingestion job lifecycle.
    Thread-safe for concurrent API requests.

    For production, replace _jobs dict with a SQLite/Redis backend.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, IngestionJob] = {}
        self._lock = Lock()

    def create_job(
        self,
        file_name: str,
        file_size_bytes: int,
        uploaded_by: str = "system",
    ) -> IngestionJob:
        """Create and register a new ingestion job."""
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            job_id=job_id,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            uploaded_by=uploaded_by,
        )
        with self._lock:
            self._jobs[job_id] = job
        logger.info(f"Created ingestion job {job_id[:8]} for file: {file_name}")
        return job

    def get_job(self, job_id: str) -> IngestionJob | None:
        """Retrieve a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(
        self,
        status: JobStatus | None = None,
        uploaded_by: str | None = None,
        limit: int = 50,
    ) -> list[IngestionJob]:
        """List jobs with optional filters."""
        with self._lock:
            jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]
        if uploaded_by:
            jobs = [j for j in jobs if j.uploaded_by == uploaded_by]

        # Most recent first
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def apply_decisions(
        self,
        job_id: str,
        decisions: list[IssueDecision],
    ) -> IngestionJob | None:
        """
        Apply HITL decisions to a job.

        If all non-auto-rejected issues are resolved → mark hitl_resolved = True.
        """
        job = self.get_job(job_id)
        if not job:
            return None
        if job.status != JobStatus.PENDING_REVIEW:
            return job

        job.issue_decisions = decisions

        # Check if all HITL issues have been decided
        hitl_security_count = 0
        hitl_pii_count = 0
        if job.security_scan:
            hitl_security_count = sum(1 for i in job.security_scan.issues if i.requires_hitl)
        if job.pii_scan:
            hitl_pii_count = len(job.pii_scan.hitl_locations)

        total_hitl = hitl_security_count + hitl_pii_count
        decided = len(decisions)

        if decided >= total_hitl:
            job.hitl_resolved = True
            # Check if any issue was outright rejected
            any_rejected = any(not d.approved for d in decisions)
            if any_rejected:
                job.set_status(JobStatus.CANCELLED)
                job.error_message = "Ingestion cancelled by reviewer: one or more issues rejected."
            else:
                job.set_status(JobStatus.APPROVED)
        else:
            job.log(f"HITL partial: {decided}/{total_hitl} issues decided. Waiting for remaining decisions.")

        return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job and clean up temp files."""
        job = self.get_job(job_id)
        if not job:
            return False
        if job.status in (JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED):
            return False

        job.set_status(JobStatus.CANCELLED)

        # Clean up temp file
        if job.temp_file_path:
            try:
                Path(job.temp_file_path).unlink(missing_ok=True)
                job.log("Temp file cleaned up.")
            except Exception as e:
                logger.warning(f"Could not delete temp file for job {job_id}: {e}")

        return True

    def cleanup_completed(self, older_than_hours: int = 24) -> int:
        """Remove completed/cancelled jobs older than N hours to prevent memory leak."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        terminal_statuses = {JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED}

        removed = 0
        with self._lock:
            to_delete = [
                jid for jid, job in self._jobs.items() if job.status in terminal_statuses and job.updated_at < cutoff
            ]
            for jid in to_delete:
                del self._jobs[jid]
                removed += 1

        if removed:
            logger.info(f"Cleaned up {removed} completed ingestion jobs.")
        return removed


# Singleton instance — shared across API requests
job_manager = IngestionJobManager()
