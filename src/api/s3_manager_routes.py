import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

import pymupdf as fitz
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from src.agents.quiz_agent import generate_quiz_and_match_step
from src.auth.dependencies import require_vinfast, require_vinfast_or_owner
from src.cloud.s3_service import s3_service
from src.content.onboarding_catalog import ROLE_ONBOARDING_CATALOG
from src.db import get_db
from src.db.crud import create_pending_updates_for_step, get_steps_by_role
from src.db.models import OnboardingStep, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/s3-manager", tags=["S3 Manager"])


def extract_text_from_pdf(filepath: str) -> str:
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}")
        return ""


@router.get("/explore")
async def explore_bucket(
    prefix: str = Query("", description="Folder prefix (e.g. 'KeToan/')"),
    current_user: User = Depends(require_vinfast_or_owner),
):
    """
    Cho phép vinfast và owner xem cây thư mục MinIO.
    """
    if not prefix.endswith("/") and prefix != "":
        prefix += "/"

    items = s3_service.explore_bucket(prefix)
    return {"prefix": prefix, "items": items}


@router.post("/upload-direct")
async def upload_direct(
    file: UploadFile = File(...),
    target_folder: str = Form("", description="Thư mục đích trên S3 (vd: 'KeToan/Hướng dẫn/')"),
    target_role: str = Form(
        "auto",
        description="Role mục tiêu: accountant/sale/technician/manager/owner/all/auto. 'auto' = tự đoán từ folder.",
    ),
    current_user: User = Depends(require_vinfast),
    db: Session = Depends(get_db),
):
    """
    Upload file vào MinIO, tự động gán metadata, chạy Contextual AI, cập nhật lộ trình.
    """
    # 1. Định hình đường dẫn trên MinIO
    if not target_folder.endswith("/"):
        target_folder += "/"
    if target_folder == "/":
        target_folder = ""

    # Loại bỏ hậu tố phiên bản (v2, version 3, v.v.) khỏi tên file
    pattern = re.compile(r"[-_\s]*(v\d+|version\s*\d+)\s*(?=\.\w+$)", re.IGNORECASE)
    base_filename = pattern.sub("", file.filename)

    # S3 sẽ lưu bằng tên gốc (có chữ v2)
    object_key = f"{target_folder}{file.filename}"
    base_object_key = f"{target_folder}{base_filename}"

    # Đoán role từ thư mục gốc (vd: 'KeToan/...' -> 'accountant')
    parts = object_key.split("/")
    root_folder = parts[0] if len(parts) > 0 else ""

    VALID_ROLES = ("accountant", "sale", "technician", "manager", "owner", "all")
    role_mapping = {
        "KeToan": "accountant",
        "KTV": "technician",
        "Sale": "sale",
        "Manager": "manager",
        "General_doc": "all",
    }
    # Nếu VinFast chọn role rõ ràng qua dropdown — dùng luôn. Nếu không, đoán từ folder.
    if target_role in VALID_ROLES:
        role = target_role
    else:
        role = role_mapping.get(root_folder, "all")
    module_name = parts[1] if len(parts) > 1 else root_folder

    # 2. Lưu file tạm
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, base_filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Upload lên MinIO với Metadata
        metadata = {"role": role, "module": urllib.parse.quote(module_name)}
        s3_service.upload_file_with_metadata(temp_path, object_key, metadata)

        # 4. Trích xuất văn bản (nếu là PDF)
        extracted_text = ""
        if base_filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(temp_path)

        # 5. Kiểm tra xem file có thuộc cấu hình chuẩn (Catalog) không bằng tên cơ sở
        s3_url = f"s3://{base_object_key}"
        is_in_catalog = False
        for role_steps in ROLE_ONBOARDING_CATALOG.values():
            for step in role_steps:
                for res in step.get("resources", []):
                    if res.get("path") == s3_url:
                        is_in_catalog = True
                        break
                if is_in_catalog:
                    break
            if is_in_catalog:
                break

        if is_in_catalog:
            # File chuẩn của hệ thống, chỉ upload lên MinIO,
            # cơ chế seed_onboarding_steps sẽ tự phục hồi bài học ở các request sau.
            return {
                "success": True,
                "message": f"Upload thành công file chuẩn {base_filename}. Lộ trình hệ thống sẽ tự động cập nhật.",
                "step_id": None,
                "is_new_step": False,
                "users_notified": 0,
            }

        # 6. Gọi Agent để xếp vào Step & Sinh Quiz (chỉ cho file mới tinh không có trong catalog)
        db_steps = get_steps_by_role(db, role)
        existing_steps = [{"id": s.id, "title": s.title, "description": s.description} for s in db_steps]

        # Ngữ cảnh thêm cho Agent (Contextual Info)
        context_info = f"Đây là file '{base_filename}' nằm trong thư mục '{module_name}' thuộc phân hệ '{root_folder}'."
        if extracted_text:
            context_info += f"\nNội dung: {extracted_text[:2000]}"

        agent_result = await generate_quiz_and_match_step(
            file_text=context_info,  # Gửi context thay vì chỉ có text
            role=role,
            filename=base_filename,
            existing_steps=existing_steps,
        )

        # Theo yêu cầu: File mới hoàn toàn -> luôn tạo Section mới (Step mới)
        is_new_step = agent_result.get("is_new_step", True)
        step_id = agent_result.get("matched_step_id")
        quiz_data = agent_result.get("quiz", [])

        resource_item = {
            "name": base_filename,
            "type": "doc" if not base_filename.lower().endswith((".mp4", ".webm")) else "video",
            "path": f"s3://{object_key}",
            "meta": "File được upload bởi VinFast",
        }

        affected_step_id = None
        notified_count = 0

        if is_new_step:
            new_title = agent_result.get("new_step_title", module_name or "Bài học mới")

            # Phân bổ vào đúng Module dựa trên thư mục
            # Module 1 (Văn hoá, Lịch sử): General_doc
            # Module 2 (Quy trình): QuyTrinh (hoặc các thư mục dùng chung không phân biệt phòng ban)
            # Module 3 (Chuyên môn): KeToan, Sale, KTV, Manager
            if root_folder == "General_doc":
                assigned_order = 1
            else:
                assigned_order = max([s.order for s in db_steps] + [0]) + 1

            new_step = OnboardingStep(
                role_target=role,
                order=assigned_order,
                title=new_title,
                short_title=new_title,
                description=f"Bài học tự động tạo từ thư mục {module_name}",
                step_type="video" if resource_item["type"] == "video" else "document",
                resource_url=resource_item["path"],
                resources=[resource_item],
                quiz=quiz_data,
                content_version="AI_GENERATED",
            )
            db.add(new_step)
            db.commit()
            db.refresh(new_step)
            affected_step_id = new_step.id
        else:
            step = db.query(OnboardingStep).filter(OnboardingStep.id == step_id).first()
            if not step:
                raise HTTPException(status_code=404, detail="Không tìm thấy bài học tương ứng.")

            current_resources = step.resources or []
            current_resources = [r for r in current_resources if r["name"] != base_filename]
            current_resources.insert(0, resource_item)

            step.resources = current_resources
            step.resource_url = resource_item["path"]
            step.quiz = quiz_data
            step.content_version = "AI_GENERATED"
            db.commit()
            affected_step_id = step.id

        # 7. Pending Updates
        notified_count = create_pending_updates_for_step(db, affected_step_id)

        return {
            "success": True,
            "message": f"Upload thành công vào {object_key}",
            "step_id": affected_step_id,
            "is_new_step": is_new_step,
            "users_notified": notified_count,
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.delete("/delete")
async def delete_file(
    object_key: str = Query(..., description="Đường dẫn file trên S3 (vd: 'KeToan/file.mp4')"),
    current_user: User = Depends(require_vinfast),
    db: Session = Depends(get_db),
):
    """
    Xóa file trên MinIO và gỡ khỏi OnboardingStep tương ứng.
    """
    success = s3_service.delete_object(object_key)
    if not success:
        raise HTTPException(status_code=500, detail="Không thể xoá file trên MinIO")

    s3_url = f"s3://{object_key}"
    steps = db.query(OnboardingStep).all()
    affected_step_id = None

    for step in steps:
        if step.resources:
            new_resources = [r for r in step.resources if r.get("path") != s3_url]
            if len(new_resources) != len(step.resources):
                if not new_resources:
                    from src.db.models import PendingUpdate, UserStepProgress

                    db.query(UserStepProgress).filter_by(step_id=step.id).delete()
                    db.query(PendingUpdate).filter_by(step_id=step.id).delete()
                    db.delete(step)
                else:
                    step.resources = new_resources
                    if step.resource_url == s3_url:
                        step.resource_url = new_resources[0]["path"]
                affected_step_id = step.id

    if affected_step_id:
        db.commit()

    return {"success": True, "message": "Đã xoá file thành công."}


# ---------------------------------------------------------------------------
# Re-index ChromaDB (Sprint 2: Trigger từ UI thay vì chạy script tay)
# ---------------------------------------------------------------------------

_reindex_running = False  # Flag đơn giản kiểm soát chạy song song


def _run_reindex_background() -> None:
    """Chạy rag_ingestion_pipeline.py như subprocess để rebuild ChromaDB + BM25."""
    global _reindex_running
    _reindex_running = True
    try:
        import pathlib

        project_root = pathlib.Path(__file__).resolve().parent.parent.parent
        script = project_root / "scripts" / "rag_ingestion_pipeline.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600,  # Tối đa 10 phút
        )
        if result.returncode != 0:
            logger.error(f"Re-index thất bại:\n{result.stderr}")
        else:
            logger.info(f"Re-index thành công:\n{result.stdout[-500:]}")
    except Exception as e:
        logger.error(f"Re-index exception: {e}", exc_info=True)
    finally:
        _reindex_running = False


@router.post("/reindex-chromadb")
async def reindex_chromadb(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_vinfast),
):
    """
    VinFast trigger re-index ChromaDB + BM25 sau khi upload/xoá tài liệu.

    💡 Giải thích cho người mới học PM:
    - Upload file lên MinIO không đủ — chatbot đọc từ ChromaDB (kho vector).
    - Endpoint này gọi lại toàn bộ pipeline ingestion ở nền (background).
    - UI sẽ nhận ngay response 202 Accepted, không cần chờ rebuild xong.
    """
    global _reindex_running
    if _reindex_running:
        return {
            "success": False,
            "message": "🔄 Hệ thống đang re-index, vui lòng chờ vài phút rồi thử lại.",
        }
    background_tasks.add_task(_run_reindex_background)
    logger.info(f"Re-index ChromaDB được kích hoạt bởi {current_user.email}")
    return {
        "success": True,
        "message": "✅ Đã bắt đầu cập nhật chatbot. Quá trình chạy ở nền, mất 2-5 phút. Chatbot sẽ tự động cập nhật khi xong.",
    }


@router.get("/reindex-status")
async def reindex_status(current_user: User = Depends(require_vinfast)):
    """Kiểm tra trạng thái re-index hiện tại."""
    return {
        "running": _reindex_running,
        "message": "🔄 Đang cập nhật chatbot..." if _reindex_running else "✅ Chatbot đã được cập nhật.",
    }


@router.post("/retry-failed")
async def retry_failed_documents(
    current_user: User = Depends(require_vinfast),
    db: Session = Depends(get_db),
):
    """
    Cho phép quản trị viên VinFast kích hoạt thử lại xử lý các file bị lỗi.
    Chuyển trạng thái từ 'failed' về 'pending' để chu kỳ đồng bộ tiếp theo xử lý.
    """
    from src.services.s3_document_service import S3DocumentService

    svc = S3DocumentService()
    count = svc.retry_failed_documents(db)
    return {
        "success": True,
        "reset_count": count,
        "message": f"✅ Đã chuyển {count} tài liệu bị lỗi về trạng thái chờ xử lý (pending).",
    }

