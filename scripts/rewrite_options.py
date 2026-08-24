import ast
import json
import os
import re

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
prompt = PromptTemplate.from_template(
    """
Bạn là một biên tập viên nội dung đào tạo chuyên nghiệp.
Dưới đây là một mảng JSON các câu trả lời trắc nghiệm (options).
Bạn cần làm cho TẤT CẢ các câu trả lời (cả đúng lẫn sai) trở nên CỰC KỲ NGẮN GỌN (tối đa 1 dòng, dưới 15 từ mỗi câu).

Yêu cầu BẮT BUỘC:
1. Đọc câu đúng (index 0). Dù nó đang dài hay ngắn, hãy CHỦ ĐỘNG TÓM TẮT VÀ CẮT GỌT nó lại thành MỘT CỤM TỪ NGẮN GỌN NHẤT CÓ THỂ (chỉ tập trung vào keyword hoặc hành động cốt lõi, tuyệt đối không giải thích dài dòng).
2. Các câu sai (index 1, 2, 3) cũng phải được gọt giũa lại hoặc viết lại sao cho NGẮN TƯƠNG ĐƯƠNG câu đúng (dưới 15 từ).
3. Đảm bảo độ dài của 4 câu là ngang bằng nhau để người học không đoán mò được.
4. KHÔNG hallucination (không bịa đặt thông tin quá sai lệch hoặc phi lý). Các câu sai chỉ là những phương án gây nhiễu, liên quan đến bối cảnh nhưng sai nghiệp vụ.
5. Tuyệt đối KHÔNG BÔI DÀI. Mọi thứ phải có thể đọc nhanh trong nháy mắt.
6. KHÔNG đổi thứ tự các câu trả lời (câu đúng vẫn phải ở index 0).
7. Chỉ trả về một mảng JSON chứa các chuỗi, không kèm Markdown, không kèm lời giải thích.

Ví dụ Input:
["Nhập hàng, bán hàng, thu tiền, hóa đơn và Claim", "Chỉ tư vấn khách tại showroom", "Chỉ sửa chữa xe tại xưởng", "Chỉ quản lý nhân sự đại lý"]

Ví dụ Output:
[
  "Xử lý nhập hàng, ghi nhận bán hàng, thu tiền, xuất hóa đơn và làm hồ sơ Claim",
  "Tư vấn trực tiếp cho khách hàng tại showroom và giải đáp thắc mắc về tính năng",
  "Thực hiện bảo dưỡng, kiểm tra lỗi và sửa chữa các dòng xe máy điện tại xưởng",
  "Quản lý lịch làm việc, phân công ca trực cho toàn bộ nhân sự khối đại lý"
]

Dữ liệu cần xử lý:
{options_json}
    """
)


def process_file():
    with open("src/content/onboarding_catalog.py", encoding="utf-8") as f:
        content = f.read()

    # Find all "options": [...] occurrences
    pattern = r'("options":\s*)(\[.*?\])(,)'
    matches = list(re.finditer(pattern, content, flags=re.DOTALL))

    print(f"Found {len(matches)} quiz options to process.")

    total = len(matches)
    processed = 0

    def replace_match(match):
        nonlocal processed
        processed += 1
        print(f"Processing {processed}/{total}...")

        prefix = match.group(1)
        options_str = match.group(2)
        suffix = match.group(3)

        # clean newlines inside the options array to evaluate
        options_str_clean = options_str.replace("\n", " ")
        try:
            options_list = ast.literal_eval(options_str_clean)
            if not isinstance(options_list, list) or len(options_list) < 2:
                return match.group(0)

            options_json = json.dumps(options_list, ensure_ascii=False)

            chain = prompt | llm
            response = chain.invoke({"options_json": options_json}).content

            # Parse the JSON response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3].strip()
            elif response.startswith("```"):
                response = response[3:-3].strip()

            new_options = json.loads(response)

            if len(new_options) != len(options_list):
                print(f"Length mismatch for {options_json}")
                return match.group(0)

            # Format the output using json.dumps to handle escaping
            formatted_options = json.dumps(new_options, ensure_ascii=False)
            return prefix + formatted_options + suffix

        except Exception as e:
            print(f"Failed to process {options_str_clean[:30]}: {e}")
            return match.group(0)

    # Use a lambda that calls replace_match to track progress
    new_content = re.sub(pattern, replace_match, content, flags=re.DOTALL)

    with open("src/content/onboarding_catalog.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Done!")


if __name__ == "__main__":
    process_file()
