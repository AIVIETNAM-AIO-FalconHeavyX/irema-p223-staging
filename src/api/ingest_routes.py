import os
import shutil
import tempfile

import pymupdf as fitz
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.agents.quiz_agent import generate_quiz_and_match_step
from src.auth.dependencies import require_manager_or_owner
from src.cloud.s3_service import s3_service
from src.db import get_db
from src.db.crud import create_pending_updates_for_step, get_steps_by_role
from src.db.models import OnboardingStep, User

router = APIRouter(prefix="/ingest", tags=["Ingest"])


def extract_text_from_pdf(filepath: str) -> str:
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    role: str = Form(...),
    current_user: User = Depends(require_manager_or_owner),
    db: Session = Depends(get_db),
):
    """
    1. Nhận file từ Chủ đại lý (Owner).
    2. Upload file lên MinIO.
    3. Đọc text từ PDF.
    4. Gọi Agent phân loại step & sinh Quiz 3 câu.
    5. Cập nhật Database (OnboardingStep).
    6. Tạo PendingUpdate cho nhân viên cũ (force quiz).
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF.")

    # 1. Lưu file tạm
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Upload lên MinIO
        object_key = s3_service.upload_raw_file(temp_path, role, file.filename)

        # 3. Trích xuất văn bản (cơ bản cho Agent)
        extracted_text = extract_text_from_pdf(temp_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Không thể trích xuất văn bản từ file PDF.")

        # 4. Gọi Agent
        # Lấy danh sách steps hiện tại của role để Agent tham chiếu
        db_steps = get_steps_by_role(db, role)
        existing_steps = [{"id": s.id, "title": s.title, "description": s.description} for s in db_steps]

        agent_result = await generate_quiz_and_match_step(
            file_text=extracted_text, role=role, filename=file.filename, existing_steps=existing_steps
        )

        step_id = agent_result.get("step_id", 0)
        is_new_step = agent_result.get("is_new_step", False) or step_id == 0
        quiz_data = agent_result.get("quiz", [])

        resource_item = {"name": file.filename, "type": "doc", "path": object_key, "meta": "File PDF mới"}

        affected_step_id = None

        if is_new_step:
            # Tạo step mới
            new_title = agent_result.get("new_step_title", "Tài liệu cập nhật")
            # Tính order mới = order cao nhất + 1
            max_order = max([s.order for s in db_steps] + [0])
            new_step = OnboardingStep(
                role_target=role,
                order=max_order + 1,
                title=new_title,
                short_title=new_title,
                description="Bài học được tạo tự động từ tài liệu mới.",
                step_type="document",
                resource_url=object_key,
                resources=[resource_item],
                quiz=quiz_data,
                content_version="AI_GENERATED",
            )
            db.add(new_step)
            db.commit()
            db.refresh(new_step)
            affected_step_id = new_step.id
        else:
            # Cập nhật step hiện tại
            step = db.query(OnboardingStep).filter(OnboardingStep.id == step_id).first()
            if not step:
                raise HTTPException(status_code=404, detail="Không tìm thấy bài học tương ứng.")

            # Cập nhật resources (thêm hoặc ghi đè)
            current_resources = step.resources or []
            # Nếu tên file đã tồn tại (hoặc tương tự), ta có thể thay thế. Ở đây thêm mới vào đầu danh sách.
            # Lọc bỏ các file cũ trùng tên (Fuzzy match đơn giản)
            current_resources = [r for r in current_resources if r["name"] != file.filename]
            current_resources.insert(0, resource_item)

            step.resources = current_resources
            step.resource_url = object_key
            step.quiz = quiz_data
            step.content_version = "AI_GENERATED"
            db.commit()
            affected_step_id = step.id

        # 5. Tạo Pending Updates cho các nhân viên đã tốt nghiệp / hoàn thành bước này
        notified_count = create_pending_updates_for_step(db, affected_step_id)

        return {
            "success": True,
            "message": "File đã được upload và xử lý thành công.",
            "step_id": affected_step_id,
            "is_new_step": is_new_step,
            "quiz_questions_generated": len(quiz_data),
            "users_notified": notified_count,
        }

    finally:
        # Xóa file tạm
        shutil.rmtree(temp_dir, ignore_errors=True)
