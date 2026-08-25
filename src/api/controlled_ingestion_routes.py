"""VinFast-admin-only controls for the durable R2 ingestion workflow."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.dependencies import require_vinfast
from src.cloud.s3_service import s3_service
from src.db import get_db
from src.db.models import User
from src.ingestion.durable import IngestionRunConflict, durable_ingestion

router = APIRouter(prefix="/api/v1/s3-manager", tags=["R2 ingestion"])


class SyncRequest(BaseModel):
    dry_run: bool = False


class RetryRequest(BaseModel):
    document_ids: list[int] | None = Field(default=None)


@router.get("/explore")
def explore_bucket(
    prefix: str = "",
    current_user: User = Depends(require_vinfast),
):
    """Read-only bucket browser retained for the admin document page."""
    normalized = prefix if prefix == "" or prefix.endswith("/") else f"{prefix}/"
    return {"prefix": normalized, "items": s3_service.explore_bucket(normalized)}


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
def start_sync(
    payload: SyncRequest | None = None,
    current_user: User = Depends(require_vinfast),
    db: Session = Depends(get_db),
):
    try:
        return durable_ingestion.start_run(
            db,
            created_by=current_user.id,
            dry_run=bool(payload and payload.dry_run),
        )
    except IngestionRunConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"R2 reconciliation failed: {error}") from error


@router.get("/sync/status")
def sync_status(current_user: User = Depends(require_vinfast), db: Session = Depends(get_db)):
    return durable_ingestion.latest_status(db)


@router.get("/documents")
def list_documents(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_vinfast),
    db: Session = Depends(get_db),
):
    try:
        documents = durable_ingestion.list_documents(db, status=status_filter, limit=limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"total": len(documents), "documents": documents}


@router.post("/retry-failed")
def retry_failed(
    payload: RetryRequest | None = None,
    current_user: User = Depends(require_vinfast),
    db: Session = Depends(get_db),
):
    try:
        return durable_ingestion.retry_failed(
            db,
            created_by=current_user.id,
            document_ids=payload.document_ids if payload else None,
        )
    except IngestionRunConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
