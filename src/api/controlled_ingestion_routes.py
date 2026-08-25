"""VinFast-admin-only controls for the durable R2 ingestion workflow."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import PurePosixPath

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.auth.dependencies import require_vinfast
from src.cloud.s3_service import s3_service
from src.db import get_db
from src.db.models import DocumentChunk, DocumentRegistry, User
from src.ingestion.durable import IngestionRunConflict, durable_ingestion

router = APIRouter(prefix="/api/v1/s3-manager", tags=["R2 ingestion"])


class SyncRequest(BaseModel):
    dry_run: bool = False


class RetryRequest(BaseModel):
    document_ids: list[int] | None = Field(default=None)


def _safe_object_key(folder: str, filename: str) -> str:
    """Build a safe POSIX R2 key and reject path traversal."""
    clean_folder = folder.replace("\\", "/").strip("/")
    parts = [part for part in clean_folder.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise HTTPException(status_code=400, detail="Invalid destination folder")
    clean_name = PurePosixPath(filename.replace("\\", "/")).name
    if not clean_name or clean_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return "/".join(parts + [clean_name])


@router.get("/explore")
def explore_bucket(
    prefix: str = "",
    current_user: User = Depends(require_vinfast),
):
    """Read-only bucket browser retained for the admin document page."""
    normalized = prefix if prefix == "" or prefix.endswith("/") else f"{prefix}/"
    return {"prefix": normalized, "items": s3_service.explore_bucket(normalized)}


@router.post("/upload-direct")
def upload_direct(
    file: UploadFile = File(...),
    target_folder: str = Form(""),
    target_role: str = Form("auto"),
    current_user: User = Depends(require_vinfast),
):
    """Upload an original document to R2; indexing is started by Sync."""
    object_key = _safe_object_key(target_folder, file.filename or "upload.bin")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=PurePosixPath(object_key).suffix) as temp:
            temp_path = temp.name
            shutil.copyfileobj(file.file, temp)
        s3_service.upload_file_with_metadata(
            temp_path,
            object_key,
            {"uploaded-by": "vinfast", "target-role": target_role or "auto"},
        )
        return {"success": True, "object_key": object_key, "message": f"Uploaded {object_key}"}
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


@router.delete("/delete")
def delete_file(
    object_key: str = Query(...),
    current_user: User = Depends(require_vinfast),
    db: Session = Depends(get_db),
):
    """Delete an R2 source and its indexed registry/chunks."""
    normalized_key = object_key.replace("\\", "/").lstrip("/")
    if not normalized_key or ".." in PurePosixPath(normalized_key).parts:
        raise HTTPException(status_code=400, detail="Invalid object key")
    if not s3_service.delete_object(normalized_key):
        raise HTTPException(status_code=502, detail="Could not delete the R2 object")
    document = db.query(DocumentRegistry).filter(DocumentRegistry.s3_key == normalized_key).first()
    if document:
        db.query(DocumentChunk).filter(DocumentChunk.document_id == str(document.id)).delete(
            synchronize_session=False
        )
        db.delete(document)
        db.commit()
    return {"success": True, "object_key": normalized_key}


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
