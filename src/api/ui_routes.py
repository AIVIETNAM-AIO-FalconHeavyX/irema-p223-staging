import json
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.api.ingestion_routes import _file_validator, _run_ingestion_pipeline
from src.ingestion.file_validator import SUPPORTED_EXTENSIONS
from src.ingestion.job_manager import job_manager

router = APIRouter(prefix="/test_input", tags=["Test UI"])

# Absolute path to workspace directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
HTML_PATH = BASE_DIR / "test_input.html"


def get_data_dirs() -> list[Path]:
    """Return all valid data directories (Data/raw is primary)."""
    dirs = []
    for candidate in [BASE_DIR / "Data" / "raw", BASE_DIR / "Data", BASE_DIR / "data" / "raw"]:
        if candidate.exists() and candidate.is_dir() and candidate not in dirs:
            dirs.append(candidate)
    return dirs


@router.get("", response_class=HTMLResponse)
async def get_test_input_ui(request: Request):
    """Serve the Test Input & Comparison Studio HTML."""
    if HTML_PATH.exists():
        return HTML_PATH.read_text(encoding="utf-8")
    return "<h1>test_input.html not found</h1>"


@router.get("/files", response_class=JSONResponse)
async def list_data_files():
    """List all valid input documents across data directories."""
    exclude_dirs = {
        "processed",
        "chroma",
        "__pycache__",
        ".git",
        "chunks",
        "cleaned_markdown",
        "metadata",
        "pii_reports",
    }
    files = []
    seen_paths = set()

    for data_dir in get_data_dirs():
        for item in data_dir.rglob("*"):
            if not item.is_file():
                continue
            if item.name.startswith(".") or item.stem.startswith("."):
                continue

            rel_parts = item.relative_to(data_dir).parts
            if any(part in exclude_dirs for part in rel_parts):
                continue

            ext = item.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            rel_path_str = str(item.relative_to(BASE_DIR)).replace("\\", "/")
            if rel_path_str in seen_paths:
                continue
            seen_paths.add(rel_path_str)

            files.append(
                {
                    "name": item.name,
                    "path": rel_path_str,
                    "size": item.stat().st_size,
                    "ext": ext,
                }
            )

    # Sort files alphabetically
    files.sort(key=lambda x: x["name"])
    return {"files": files}


@router.get("/raw_file")
async def get_raw_file(path: str):
    """Stream raw input file for in-browser visual inspection (PDF, images, text)."""
    target = (BASE_DIR / path).resolve()
    if not target.exists() or not target.is_file():
        # Try finding in Data/ or data/
        for d in get_data_dirs():
            candidate = (d / path).resolve()
            if candidate.exists() and candidate.is_file():
                target = candidate
                break

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    ext = target.suffix.lower()
    media_type = "application/octet-stream"
    if ext == ".pdf":
        media_type = "application/pdf"
    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
        media_type = f"image/{ext.lstrip('.')}"
    elif ext in [".txt", ".md", ".json", ".csv"]:
        media_type = "text/plain; charset=utf-8"

    from fastapi.responses import StreamingResponse

    ascii_clean = "".join(c for c in target.name if c.isascii() and c not in '"\r\n') or f"document{ext}"

    def iterfile():
        with open(target, mode="rb") as file_like:
            while chunk := file_like.read(64 * 1024):
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{ascii_clean}"'},
    )


@router.get("/job_result/{job_id}", response_class=JSONResponse)
async def get_job_result(job_id: str):
    """Retrieve full output artifacts (Markdown, Chunks JSON, Metadata) for inspection."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    markdown_content = ""
    chunks = []

    # 1. Read Markdown Output
    if job.output_markdown_path and Path(job.output_markdown_path).exists():
        try:
            markdown_content = Path(job.output_markdown_path).read_text(encoding="utf-8")
        except Exception:
            pass

    # 2. Find Chunks JSON in data/processed/chunks or Data/processed/chunks
    if job.file_name:
        stem = Path(job.file_name).stem
        for p in [BASE_DIR / "Data" / "processed" / "chunks", BASE_DIR / "data" / "processed" / "chunks"]:
            if p.exists():
                for chunk_file in p.rglob("*.json"):
                    if stem in chunk_file.stem or chunk_file.stem in stem:
                        try:
                            chunks = json.loads(chunk_file.read_text(encoding="utf-8"))
                            break
                        except Exception:
                            pass
            if chunks:
                break

    preview = job.to_preview_dict()
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "file_name": job.file_name,
        "markdown": markdown_content,
        "chunks": chunks,
        "chunks_count": len(chunks) or job.chunks_count,
        "logs": job.processing_log,
        "security_issues": preview.get("security_issues", []),
        "pii_hitl_issues": preview.get("pii_hitl_issues", []),
    }


class ProcessLocalRequest(BaseModel):
    path: str
    auto_approve: bool = False


@router.post("/process_local", response_class=JSONResponse)
async def process_local_file(req: ProcessLocalRequest, background_tasks: BackgroundTasks):
    """Process a local file from the data directory for testing."""
    file_path = (BASE_DIR / req.path).resolve()
    if not file_path.exists() or not file_path.is_file():
        for d in get_data_dirs():
            candidate = (d / req.path).resolve()
            if candidate.exists() and candidate.is_file():
                file_path = candidate
                break

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found in data directory.")

    suffix = file_path.suffix.lower()
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.close()
        tmp_path = Path(tmp.name)
        shutil.copy2(file_path, tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy file: {e}")

    validation = _file_validator.validate(tmp_path)
    if not validation.is_valid:
        tmp_path.unlink(missing_ok=True)
        return JSONResponse(
            status_code=422,
            content={
                "status": "REJECTED",
                "reason": "File validation failed",
                "errors": validation.errors,
                "warnings": validation.warnings,
            },
        )

    job = job_manager.create_job(
        file_name=file_path.name,
        file_size_bytes=file_path.stat().st_size,
        uploaded_by="test_ui",
    )
    job.temp_file_path = str(tmp_path)
    if validation.warnings:
        for w in validation.warnings:
            job.log(f"WARNING: {w}")

    background_tasks.add_task(
        _run_ingestion_pipeline,
        job_id=job.job_id,
        tmp_path=tmp_path,
        original_filename=file_path.name,
        auto_approve=req.auto_approve,
    )

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job.job_id,
            "status": job.status.value,
            "message": f"Local file '{file_path.name}' accepted.",
        },
    )
