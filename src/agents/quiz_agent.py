import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.services.llm import get_llm

logger = logging.getLogger(__name__)


async def generate_quiz_and_match_step(
    file_text: str, role: str, filename: str, existing_steps: list[dict]
) -> dict[str, Any]:
    """
    Đọc nội dung tài liệu (file_text), so khớp với danh sách các bài học hiện có của role,
    và sinh ra 3 câu hỏi Quiz.

    Args:
        file_text (str): Nội dung trích xuất từ file (PDF/Docx).
        role (str): Vai trò do Admin chọn.
        filename (str): Tên file.
        existing_steps (list[dict]): Danh sách các step hiện có, format: [{"id": 1, "title": "...", "description": "..."}, ...]

    Returns:
        dict: Chứa `step_id` (int), `is_new_step` (bool), `new_step_title` (str), `quiz` (list[dict]).
    """
    llm = get_llm()

    # Cắt ngắn file_text nếu quá dài (lấy 15000 ký tự đầu tiên để không vượt quá context window)
    content_snippet = file_text[:15000]

    system_prompt = """Bạn là một Chuyên gia Đào tạo của VinFast.
Nhiệm vụ của bạn là đọc thông tin về một tài liệu mới (có thể bao gồm tên file, thư mục, và nội dung trích xuất nếu có) và thực hiện 2 việc:

1. PHÂN LOẠI TÀI LIỆU (STEP MATCHING):
Dựa vào danh sách các bài học (Steps) hiện có của hệ thống cho Role này.
Hãy chọn `step_id` phù hợp nhất với tài liệu. Nếu nội dung hoàn toàn mới và không thuộc bất kỳ step nào, hãy trả về `step_id: 0` và cung cấp một tiêu đề ngắn gọn cho bài học mới trong `new_step_title`.

2. TẠO CÂU HỎI TRẮC NGHIỆM (QUIZ GENERATION):
Tạo đúng 3 câu hỏi trắc nghiệm (Multiple Choice) để kiểm tra kiến thức của nhân viên dựa trên thông tin được cung cấp.
Nếu tài liệu là Video hoặc không có nội dung trích xuất, hãy tạo 3 câu hỏi chung chung liên quan đến chủ đề của tên file hoặc tên thư mục (ví dụ: "Mục đích chính của hướng dẫn này là gì?", "Bạn cần lưu ý điều gì nhất khi thực hiện quy trình này?").
Mỗi câu hỏi phải có 4 lựa chọn, chỉ 1 đáp án đúng, và có lời giải thích.

BẮT BUỘC TRẢ VỀ CHUẨN JSON (Không có markdown block, không có text dư thừa) theo cấu trúc sau:
{
  "step_id": 12,
  "is_new_step": false,
  "new_step_title": "",
  "quiz": [
    {
      "id": 1,
      "question": "Nội dung câu hỏi?",
      "options": ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"],
      "correctIndex": 0,
      "explanation": "Giải thích vì sao A đúng."
    }
  ]
}
"""

    user_prompt = f"""Role: {role.upper()}
Filename: {filename}

Danh sách các bài học (Steps) hiện có:
{json.dumps(existing_steps, ensure_ascii=False, indent=2)}

Ngữ cảnh / Nội dung tài liệu:
{content_snippet}

Hãy thực hiện nhiệm vụ và chỉ trả về chuỗi JSON hợp lệ.
"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    try:
        response = llm.invoke(messages)
        # Parse JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]

        result = json.loads(content.strip())
        return result
    except Exception as e:
        logger.error(f"Lỗi khi Agent sinh Quiz: {e}")
        # Fallback an toàn nếu LLM lỗi
        return {
            "step_id": existing_steps[0]["id"] if existing_steps else 0,
            "is_new_step": False,
            "new_step_title": "Tài liệu mới",
            "quiz": [
                {
                    "id": 1,
                    "question": "Bạn đã đọc kỹ và hiểu rõ các nội dung trong tài liệu mới này chưa?",
                    "options": ["Tôi đã hiểu", "Tôi chưa hiểu", "Cần quản lý hỗ trợ", "Chưa đọc"],
                    "correctIndex": 0,
                    "explanation": "Nhân viên bắt buộc phải đọc và nắm rõ tài liệu cập nhật.",
                }
            ],
        }
