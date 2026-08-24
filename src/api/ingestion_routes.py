from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.ingestion.file_validator import FileValidator
from src.ingestion.job_manager import IngestionJob, IssueDecision, JobStatus, job_manager
from src.ingestion.pii_scanner import PIIScanner
from src.ingestion.security_scanner import SecurityScanner
from src.preprocess.markdown_pipeline import MarkdownProcessingPipeline as MarkdownPipeline
from src.preprocess.pipeline import PreprocessingPipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])

# Module-level singletons
_file_validator = FileValidator()
_security_scanner = SecurityScanner()
_pii_scanner = PIIScanner()
_preprocessing_pipeline = PreprocessingPipeline()


# ===========================================================================
# POST /api/v1/ingest/upload
# ===========================================================================


@router.post("/upload", summary="Upload và bắt đầu ingestion một tài liệu")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Tài liệu cần nhập (PDF, DOCX, PPTX, XLSX, MP4, WEBM, TXT)")],
    uploaded_by: Annotated[str, Form(description="Tên hoặc ID người nhập liệu")] = "anonymous",
    auto_approve: Annotated[bool, Form(description="Tự động approve tất cả issues (chỉ dùng cho CI/CD)")] = False,
) -> JSONResponse:
    """
    Upload một tài liệu và khởi chạy toàn bộ ingestion pipeline:
    1. Validate file (extension, magic bytes, size, zip-bomb)
    2. Tạo Ingestion Job và trả về job_id ngay lập tức
    3. Chạy Extract → Security Scan → PII Scan ở background
    4. Nếu phát hiện vấn đề → chuyển sang PENDING_REVIEW
    5. Nếu auto_approve=True hoặc không có vấn đề → tiếp tục Chunk + Index ngay
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    # Save to temp file first to allow validation
    suffix = Path(file.filename).suffix.lower()
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        contents = await file.read()
        tmp.write(contents)
        tmp.flush()
        tmp.close()
        tmp_path = Path(tmp.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # --- 1. File Validation (synchronous, fast) ---
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

    # --- 2. Create Job ---
    job = job_manager.create_job(
        file_name=file.filename,
        file_size_bytes=len(contents),
        uploaded_by=uploaded_by,
    )
    job.temp_file_path = str(tmp_path)
    if validation.warnings:
        for w in validation.warnings:
            job.log(f"WARNING: {w}")

    # --- 3. Schedule background processing ---
    background_tasks.add_task(
        _run_ingestion_pipeline,
        job_id=job.job_id,
        tmp_path=tmp_path,
        original_filename=file.filename,
        auto_approve=auto_approve,
    )

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job.job_id,
            "status": job.status.value,
            "message": (f"File '{file.filename}' accepted. Track progress at GET /api/v1/ingest/jobs/{job.job_id}"),
        },
    )


# ===========================================================================
# GET /api/v1/ingest/jobs/{job_id}
# ===========================================================================


@router.get("/jobs/{job_id}", summary="Kiểm tra trạng thái Ingestion Job")
async def get_job_status(job_id: str) -> JSONResponse:
    """Trả về trạng thái ngắn gọn của một ingestion job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JSONResponse(content=job.to_summary_dict())


# ===========================================================================
# GET /api/v1/ingest/jobs/{job_id}/preview
# ===========================================================================


@router.get("/jobs/{job_id}/preview", summary="Xem chi tiết kết quả scan để HITL review")
async def get_job_preview(job_id: str) -> JSONResponse:
    """
    Trả về kết quả đầy đủ để người nhập liệu review trước khi approve:
    - Danh sách Security Issues (với vị trí và đoạn trích văn bản)
    - Danh sách PII cần HITL (confidence thấp, có context trước/sau)
    - Preview 500 ký tự đầu của nội dung đã extract
    - Log xử lý
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    if job.status not in (JobStatus.PENDING_REVIEW, JobStatus.APPROVED, JobStatus.DONE):
        return JSONResponse(
            status_code=200,
            content={
                **job.to_summary_dict(),
                "message": f"Job is currently in status '{job.status.value}'. Preview available after SCANNING.",
            },
        )

    return JSONResponse(content=job.to_preview_dict())


# ===========================================================================
# POST /api/v1/ingest/jobs/{job_id}/approve
# ===========================================================================


@router.post("/jobs/{job_id}/approve", summary="Gửi quyết định HITL để approve/reject từng issue")
async def approve_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    decisions: list[dict],
) -> JSONResponse:
    """
    Gửi quyết định của người review cho từng issue trong danh sách HITL.

    Body (JSON array):
    ```json
    [
      {"issue_index": 0, "approved": true, "reviewer_note": "Số điện thoại này là ví dụ minh họa"},
      {"issue_index": 1, "approved": false, "reviewer_note": "Đây là thông tin khách hàng thật, cần xóa"}
    ]
    ```

    - Nếu tất cả decisions.approved=True → tiếp tục Chunk + Index
    - Nếu có decision.approved=False → hủy job và xóa file
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.status != JobStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=409,
            detail=f"Job status is '{job.status.value}'. Only PENDING_REVIEW jobs can be approved.",
        )

    parsed_decisions = [
        IssueDecision(
            issue_index=d.get("issue_index", 0),
            approved=bool(d.get("approved", True)),
            reviewer_note=d.get("reviewer_note", ""),
        )
        for d in decisions
    ]

    updated_job = job_manager.apply_decisions(job_id, parsed_decisions)
    if not updated_job:
        raise HTTPException(status_code=500, detail="Failed to apply decisions.")

    if updated_job.status == JobStatus.APPROVED:
        # Proceed to chunking + indexing
        background_tasks.add_task(_run_chunking_and_indexing, job_id=job_id)
        return JSONResponse(
            content={
                **updated_job.to_summary_dict(),
                "message": "All issues approved. Chunking and indexing started.",
            }
        )
    elif updated_job.status == JobStatus.CANCELLED:
        return JSONResponse(
            status_code=200,
            content={
                **updated_job.to_summary_dict(),
                "message": "Job cancelled: one or more issues were rejected by reviewer.",
            },
        )
    else:
        return JSONResponse(
            content={
                **updated_job.to_summary_dict(),
                "message": "Decisions recorded. Awaiting remaining issue decisions.",
            }
        )


# ===========================================================================
# POST /api/v1/ingest/jobs/{job_id}/cancel
# ===========================================================================


@router.post("/jobs/{job_id}/cancel", summary="Hủy một Ingestion Job")
async def cancel_job(job_id: str) -> JSONResponse:
    """Hủy job và xóa file tạm."""
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found or already in terminal state.",
        )
    return JSONResponse(content={"job_id": job_id, "status": "CANCELLED"})


# ===========================================================================
# GET /api/v1/ingest/jobs (list)
# ===========================================================================


@router.get("/jobs", summary="Liệt kê tất cả Ingestion Jobs")
async def list_jobs(
    status: str | None = None,
    uploaded_by: str | None = None,
    limit: int = 20,
) -> JSONResponse:
    """Liệt kê các ingestion jobs, có thể lọc theo status và người upload."""
    try:
        status_enum = JobStatus(status) if status else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status value: '{status}'.")

    jobs = job_manager.list_jobs(status=status_enum, uploaded_by=uploaded_by, limit=limit)
    return JSONResponse(
        content={
            "total": len(jobs),
            "jobs": [j.to_summary_dict() for j in jobs],
        }
    )


# ===========================================================================
# Background Processing Functions
# ===========================================================================


async def _run_ingestion_pipeline(
    job_id: str,
    tmp_path: Path,
    original_filename: str,
    auto_approve: bool,
) -> None:
    """Background task: Extract → Security Scan → PII Scan → HITL or Auto-approve."""
    job = job_manager.get_job(job_id)
    if not job:
        return

    try:
        # --- Extraction ---
        job.set_status(JobStatus.EXTRACTING)
        ext = Path(original_filename).suffix.lower()

        # .md and .txt files go directly to the markdown pipeline — no extraction needed
        if ext in (".md", ".txt"):
            job.log(f"File type '{ext}' detected — routing directly to Markdown pipeline.")
            job.set_status(JobStatus.APPROVED)
            await _run_chunking_and_indexing(job_id=job_id, source_path=tmp_path, original_filename=original_filename)
            return

        extractor = _preprocessing_pipeline.extractors.get(ext)

        if not extractor:
            job.set_status(JobStatus.FAILED)
            job.error_message = f"No extractor available for file type '{ext}'."
            return

        role, category, access_scope = _preprocessing_pipeline.detect_role_and_scope(tmp_path)
        doc = extractor.extract(tmp_path, role=role, category=category)
        doc.access_scope = access_scope
        doc.file_hash = _preprocessing_pipeline.compute_file_hash(tmp_path)
        job.file_hash = doc.file_hash

        # Build sections list for scanning
        sections = [
            {"title": s.title or f"Section {i}", "content": s.content} for i, s in enumerate(doc.sections) if s.content
        ]
        full_text = "\n\n".join(s["content"] for s in sections)
        job.extracted_text_preview = full_text[:500]

        # --- Security Scan ---
        job.set_status(JobStatus.SCANNING)
        sec_result = _security_scanner.scan_file(tmp_path, extracted_text=full_text)
        job.security_scan = sec_result

        if sec_result.has_auto_reject:
            job.set_status(JobStatus.FAILED)
            job.error_message = (
                "Document automatically rejected: contains confirmed malicious content. "
                f"Issues: {[i.issue_type for i in sec_result.issues if i.auto_rejected]}"
            )
            _cleanup_temp(job)
            return

        # --- PII Scan ---
        pii_result = _pii_scanner.scan_sections(sections)
        job.pii_scan = pii_result

        # --- Determine if HITL needed ---
        needs_hitl = (sec_result.requires_hitl or pii_result.hitl_required) and not auto_approve

        if needs_hitl:
            job.hitl_required = True
            job.set_status(JobStatus.PENDING_REVIEW)
            job.log(
                f"HITL required: {sec_result.high_count} security HIGH, "
                f"{sec_result.medium_count} MEDIUM, "
                f"{len(pii_result.hitl_locations)} PII low-confidence."
            )
            return

        # --- Auto-approve: proceed to chunking ---
        job.set_status(JobStatus.APPROVED)
        await _run_chunking_and_indexing(job_id=job_id)

    except Exception as e:
        logger.exception(f"Ingestion pipeline error for job {job_id}: {e}")
        job = job_manager.get_job(job_id)
        if job:
            job.set_status(JobStatus.FAILED)
            job.error_message = str(e)
            _cleanup_temp(job)


async def _run_chunking_and_indexing(
    job_id: str, source_path: Path | None = None, original_filename: str | None = None
) -> None:
    """Background task: run Markdown pipeline → Chunk → Embed → Index."""
    job = job_manager.get_job(job_id)
    if not job:
        return

    try:
        # Use provided source_path (for .md/.txt direct routing) or fallback to temp file
        if source_path is not None:
            tmp_path = source_path
        else:
            tmp_path = Path(job.temp_file_path)

        if not tmp_path.exists():
            job.set_status(JobStatus.FAILED)
            job.error_message = "Temp file no longer exists."
            return

        ext = tmp_path.suffix.lower()

        # ── Path A: .md / .txt ── skip PreprocessingPipeline, go straight to MarkdownPipeline
        if ext in (".md", ".txt"):
            job.set_status(JobStatus.CHUNKING)
            md_pipeline = MarkdownPipeline()
            result = md_pipeline.process_markdown_file(tmp_path)
            if not result:
                job.set_status(JobStatus.FAILED)
                job.error_message = "MarkdownProcessingPipeline returned no output."
                _cleanup_temp(job)
                return
            out_md_path, out_chunks_path = result
            job.output_markdown_path = str(out_md_path)
            # Read chunks count from output JSON
            try:
                import json as _json

                chunks_data = _json.loads(out_chunks_path.read_text(encoding="utf-8"))
                job.chunks_count = len(chunks_data)
            except Exception:
                job.chunks_count = 0
            job.indexed_count = job.chunks_count
            job.set_status(JobStatus.DONE)
            job.log(f"Ingestion complete: {job.chunks_count} chunks created and indexed.")
            _cleanup_temp(job)
            return

        # ── Path B: Binary files (PDF/DOCX/PPTX/XLSX/MP4/WEBM) ──
        # Move temp file to raw_dir under correct category structure
        raw_dir = _preprocessing_pipeline.raw_dir
        target_dir = raw_dir / "General_doc"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / job.file_name

        shutil.copy2(tmp_path, target_path)

        # Run full preprocessing (Extract → PII → Markdown output)
        job.set_status(JobStatus.CHUNKING)
        result = _preprocessing_pipeline.process_file(target_path)

        if not result:
            job.set_status(JobStatus.FAILED)
            job.error_message = "Preprocessing pipeline returned no output."
            _cleanup_temp(job)
            return

        md_path, meta_path, _ = result
        job.output_markdown_path = str(md_path)
        job.output_metadata_path = str(meta_path)

        # Run markdown pipeline (chunking)
        job.set_status(JobStatus.INDEXING)
        md_pipeline = MarkdownPipeline()
        md_result = md_pipeline.process_markdown_file(md_path)
        if md_result:
            _, out_chunks_path = md_result
            try:
                import json as _json

                chunks_data = _json.loads(out_chunks_path.read_text(encoding="utf-8"))
                job.chunks_count = len(chunks_data)
            except Exception:
                job.chunks_count = 0
        else:
            job.chunks_count = 0
        job.indexed_count = job.chunks_count

        job.set_status(JobStatus.DONE)
        job.log(f"Ingestion complete: {job.chunks_count} chunks created and indexed.")
        _cleanup_temp(job)

    except Exception as e:
        logger.exception(f"Chunking/indexing error for job {job_id}: {e}")
        job = job_manager.get_job(job_id)
        if job:
            job.set_status(JobStatus.FAILED)
            job.error_message = str(e)
            _cleanup_temp(job)


def _cleanup_temp(job: IngestionJob) -> None:
    """Delete the temporary uploaded file."""
    if job.temp_file_path:
        try:
            Path(job.temp_file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not clean temp file for job {job.job_id}: {e}")
