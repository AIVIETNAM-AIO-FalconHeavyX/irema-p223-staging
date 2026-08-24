"""Catalog lộ trình onboarding — bám sát `implementation_plan.md`.

`implementation_plan.md` ở gốc repo là **bản đặc tả nghiệp vụ**; file này là bản
thi hành của nó. Mỗi bước ở đây tương ứng 1-1 với một khối `### 📍 BƯỚC N` trong
plan: cùng tiêu đề, cùng mục tiêu, cùng hướng dẫn nhanh, cùng tài liệu, cùng câu
hỏi. `seed_onboarding_steps()` nạp catalog này vào bảng `onboarding_steps`;
frontend chỉ đọc lại qua API chứ không giữ nội dung nghiệp vụ nào.
"""

from __future__ import annotations

import unicodedata
from functools import cache

QUIZ_QUESTIONS_PER_STEP = 3
CATALOG_VERSION = "2026.08.20-minio-v2"

COMMON_OVERVIEW_RESOURCES = [
    {
        "name": "1. Tài liệu Tự hào VinGroup",
        "type": "doc",
        "path": "s3://General_doc/TaiLieuChung/1. Tài liệu Tự hào VinGroup.pdf",
    },
    {
        "name": "2. Lịch sử & Tổng quan sản phẩm XMĐ",
        "type": "doc",
        "path": "s3://General_doc/TaiLieuChung/2. Lịch sử & Tổng quan sản phẩm XMĐ_260617.pdf",
    },
]

CHAM_SOC_XE_RESOURCES = [
    {
        "name": "Đào tạo Chương trình chăm sóc xe miễn phí",
        "type": "doc",
        "path": "s3://General_doc/CTKM/Đào tạo Chương trình chăm sóc xe miễn phí_0043.pptx",
    },
    {
        "name": "VF_HDSD Chương trình chăm sóc xe miễn phí",
        "type": "doc",
        "path": "s3://KTV/VF_HDSD_HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0_7748.docx",
    },
]


def _video(name: str, path: str) -> dict:
    return {"name": name, "type": "video", "path": path}


def _doc(name: str, path: str) -> dict:
    return {"name": name, "type": "doc", "path": path}


ROLE_ONBOARDING_CATALOG: dict[str, list[dict]] = {
    "accountant": [
        {
            "duration_minutes": 2,
            "goal": "Nắm luồng công việc tổng thể của Kế toán tại đại lý XMĐ VinFast và biết cách đăng "
            "nhập, điều hướng hệ thống DMS.",
            "guides": [
                {
                    "desc": "Nhập hàng + Bán hàng + Thu tiền + Hóa đơn + Claim — KHÔNG trực tiếp tư vấn khách.",
                    "letter": "A",
                    "title": "Kế toán phụ trách gì?",
                },
                {
                    "desc": "URL → Tên đăng nhập → Chọn đại lý → Vào giao diện Trang chủ.",
                    "letter": "B",
                    "title": "Đăng nhập DMS",
                },
                {
                    "desc": "Dùng tính năng Kho tài liệu trong DMS để tải hướng dẫn cập nhật nhất.",
                    "letter": "C",
                    "title": "Tra cứu tài liệu nội bộ",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Kế toán phụ trách toàn trình chứng từ, nhưng không trực tiếp "
                    "tư vấn bán hàng cho khách.",
                    "id": 1,
                    "options": [
                        "Xử lý nhập hàng, bán hàng, thu tiền, xuất hóa đơn và Claim",
                        "Tư vấn khách hàng tại showroom về sản phẩm và dịch vụ",
                        "Bảo trì, kiểm tra và sửa chữa xe tại xưởng chất lượng",
                        "Quản lý lịch làm việc và phân công nhiệm vụ nhân sự",
                    ],
                    "question": "Kế toán chịu trách nhiệm bước nào trong luồng bán xe XMĐ?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Kho tài liệu DMS là nơi VF cập nhật hướng dẫn và biểu mẫu bản mới nhất.",
                    "id": 2,
                    "options": [
                        "Kho tài liệu DMS cung cấp hướng dẫn, quy trình và thông tin cho nhân viên",
                        "Hộp thư nội bộ cho phép gửi và nhận thông tin từ các bộ phận khác",
                        "Nhóm chat đại lý để nhân viên trao đổi và cập nhật công việc hàng ngày",
                        "Tìm kiếm trình duyệt giúp truy cập nhanh thông tin và tài liệu trực tuyến",
                    ],
                    "question": "Tìm tài liệu hướng dẫn trên DMS bằng chức năng nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Đây là 4 giai đoạn xuyên suốt mà kế toán đại lý phải kiểm soát.",
                    "id": 3,
                    "options": [
                        "Bán xe, hoàn tất giấy tờ, thu tiền và xử lý Claim chuyên nghiệp",
                        "Chỉ bán xe mà không hoàn tất các bước tiếp theo",
                        "Thu tiền trước khi có đơn hàng chính thức gây nhầm lẫn",
                        "Xử lý Claim trước khi bán xe gây vấn đề trong quy trình",
                    ],
                    "question": "Luồng tổng thể từ bán xe đến khi tiền về đại lý gồm giai đoạn nào?",
                },
            ],
            "resources": [
                {
                    "name": "1. Tài liệu Tự hào VinGroup",
                    "path": "s3://General_doc/TaiLieuChung/1. Tài liệu Tự hào VinGroup.pdf",
                    "type": "doc",
                },
                {
                    "name": "2. Lịch sử & Tổng quan sản phẩm XMĐ",
                    "path": "s3://General_doc/TaiLieuChung/2. Lịch sử & Tổng quan sản phẩm XMĐ_260617.pdf",
                    "type": "doc",
                },
            ],
            "short_title": "Tổng quan Kế toán",
            "step_type": "document",
            "title": "Chào mừng & Tổng quan quy trình Kế toán",
        },
        {
            "duration_minutes": 3,
            "goal": "Tạo được PO mua Xe XMĐ, PO Phụ tùng, PO Pin kèm xe. Phát hành Phiếu nhập kho PR khi "
            "hàng về. Biết chuyển vị trí phụ tùng trong kho và kiểm tra tồn kho phụ tùng.",
            "guides": [
                {
                    "desc": "Mua hàng → Thêm mới → Nhập thông tin xe, số lượng, mã đại lý → Gửi duyệt VinFast.",
                    "letter": "A",
                    "title": "Tạo PO Xe (mã ZVOR)",
                },
                {
                    "desc": "Tương tự PO Xe, chú ý chọn đúng loại mã hàng (phụ tùng/pin).",
                    "letter": "B",
                    "title": "Tạo PO Phụ tùng / PO Pin kèm xe",
                },
                {
                    "desc": "Phiếu nhập kho → Dán mã PO → Xác nhận số lượng thực nhận → Chuyển sang 'Phát hành' → Lưu.",
                    "letter": "C",
                    "title": "Phát hành PR khi hàng về",
                },
                {
                    "desc": "Xem tồn kho phụ tùng → Chuyển kho nếu hàng để sai vị trí.",
                    "letter": "D",
                    "title": "Kiểm tra tồn & chuyển vị trí",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Đơn mua xe/phụ tùng/pin mới từ nhà máy VF sử dụng loại chứng từ ZVOR.",
                    "id": 1,
                    "options": [
                        "ZVOR là thuật ngữ quan trọng trong quản lý quy trình và tiêu chuẩn.",
                        "ZSO1 là mã sản phẩm không có ý nghĩa trong quản lý.",
                        "ZRET là thuật ngữ không chính thức, không liên quan quy trình.",
                        "ZWAR là mã không rõ, chỉ tài liệu không chính thức trong quản lý.",
                    ],
                    "question": "Mã loại đơn hàng khi tạo PO mua xe XMĐ là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Chỉ khi phiếu PR được phát hành thì hàng mới ghi tăng vào tồn kho DMS.",
                    "id": 2,
                    "options": [
                        "Lập Phiếu nhập kho PR và chuyển sang trạng thái Phát hành.",
                        "Xuất hóa đơn ngay sau giao dịch để đảm bảo tính hợp lệ.",
                        "Tạo PO mới với thông tin đầy đủ để quản lý đơn hàng.",
                        "Gửi hồ sơ Claim cho VF kèm tài liệu cần thiết để xử lý.",
                    ],
                    "question": "Sau khi hàng về, bước tiếp theo để nhập kho là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Cùng thao tác như PO Xe, nhưng phải chọn đúng loại mã hàng (phụ tùng hay pin).",
                    "id": 3,
                    "options": [
                        "Khác nhau ở loại mã hàng, ảnh hưởng quy trình xử lý đơn hàng",
                        "Không có sự khác biệt giữa các loại đơn hàng, xử lý giống nhau",
                        "Khác nhau ở màu sắc giao diện, ảnh hưởng trải nghiệm người dùng",
                        "Khác nhau ở người phê duyệt cuối cùng, quyết định bước tiếp theo",
                    ],
                    "question": "PO Pin kèm xe khác PO Phụ tùng ở điểm nào khi tạo trên DMS?",
                },
            ],
            "resources": [
                {
                    "name": "1. Đơn đặt hàng PO XMĐ",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/1. Đơn đặt hàng PO XMĐ.mp4",
                    "type": "video",
                },
                {
                    "name": "2. Đơn đặt hàng PO phụ tùng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/2. Đơn đặt hàng PO phụ tùng.mp4",
                    "type": "video",
                },
                {
                    "name": "3. Đơn đặt hàng PO PIN kèm xe",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/3. Đơn đặt hàng PO PIN kèm xe.mp4",
                    "type": "video",
                },
                {
                    "name": "4. Phiếu nhập kho PR",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/4. Phiếu nhập kho PR.mp4",
                    "type": "video",
                },
                {
                    "name": "Hướng dẫn tạo Đơn mua hàng xe",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/Document/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE.docx",
                    "type": "doc",
                },
                {
                    "name": "Hướng dẫn tạo Đơn mua hàng phụ tùng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/Document/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG.docx",
                    "type": "doc",
                },
                {
                    "name": "Hướng dẫn tạo PO đặt Pin kèm xe",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/Document/HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE.docx",
                    "type": "doc",
                },
                {
                    "name": "Hướng dẫn chuyển vị trí phụ tùng trong kho DMS",
                    "path": "KeToan/Hướng dẫn chuyển vị trí cho các phụ tùng trong kho DMS.docx",
                    "type": "doc",
                },
                {
                    "name": "Luồng đặt hàng phụ tùng trong Danh sách cho phép",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/1. Nhập hàng/Document/Luồng đặt hàng phụ tùng trong Danh sách cho phép.docx",
                    "type": "doc",
                },
                {
                    "name": "1. Kiểm tra và xuất số lượng tồn kho phụ tùng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/3. Xem tồn/1. Kiểm tra và xuất số lượng tồn kho phụ tùng.mp4",
                    "type": "video",
                },
            ],
            "short_title": "Đặt hàng & Nhập kho",
            "step_type": "task",
            "title": "Quản lý Đặt hàng (PO) & Nhập kho (PR)",
        },
        {
            "duration_minutes": 3,
            "goal": "Thực hiện toàn bộ luồng bán hàng XMĐ cải tiến mới: Tạo Lead → Cơ hội → Đơn tổng → "
            "Chọn gói Pin → Convert → Ghép VIN → Phát hành đơn → Ký HĐTP Pin & biên bản giao "
            "pin.",
            "guides": [
                {
                    "desc": "Kiểm tra trùng theo quy luật của DMS rồi mới tạo mới.",
                    "letter": "A",
                    "title": "Tạo Khách hàng tiềm năng (Lead)",
                },
                {
                    "desc": "Chọn Battery Option cho đơn: Thuê pin hoặc Mua đứt pin.",
                    "letter": "B",
                    "title": "Tạo Cơ hội → Đơn hàng tổng",
                },
                {
                    "desc": "Convert đơn hàng XMĐ → Phát hành đơn → Ghép số khung VIN trong kho xe vào đơn.",
                    "letter": "C",
                    "title": "Convert & Ghép VIN",
                },
                {
                    "desc": "Tạo HĐTP → In hợp đồng → Khách ký biên bản bàn giao pin.",
                    "letter": "D",
                    "title": "Hợp đồng thuê Pin LFP",
                },
                {
                    "desc": "Thao tác theo bộ tài liệu hướng dẫn luồng cải tiến App XMĐ bản 2026 mới nhất.",
                    "letter": "E",
                    "title": "Lưu ý luồng cải tiến mới",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Battery Option (Thuê pin / Mua đứt pin) phải chọn ngay ở bước tạo Đơn hàng tổng.",
                    "id": 1,
                    "options": [
                        "Đảm bảo dữ liệu chính xác trước khi Convert Đơn hàng tổng",
                        "Nhận phản hồi từ khách hàng sau khi giao xe hoàn tất",
                        "Thu thập đầy đủ thông tin khi lập hồ sơ Claim",
                        "Kiểm tra số lượng và chất lượng hàng trước khi nhập kho",
                    ],
                    "question": "Chọn gói Battery Option ở bước nào trong đơn hàng DMS?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Có bộ tài liệu riêng cho Thanh lý/Chấm dứt/Đổi chủ HĐTP kèm "
                    "biên bản khách phải ký.",
                    "id": 2,
                    "options": [
                        "Thực hiện thủ tục thanh lý hợp đồng theo giấy tờ khách hàng đã ký",
                        "Xóa hợp đồng mà không kiểm tra thông tin hợp lệ",
                        "Không thực hiện hành động nào với hợp đồng hiện tại",
                        "Sửa đổi nội dung hợp đồng cũ mà không có sự đồng ý",
                    ],
                    "question": "Muốn hủy HĐTP khi khách đổi xe, Kế toán cần làm thủ tục gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Đơn phải được convert và phát hành thì mới ghép được số khung VIN từ kho xe.",
                    "id": 3,
                    "options": [
                        "Hoàn tất Convert và phát hành đơn hàng cho khách hàng",
                        "Liên hệ và tư vấn khách hàng ngay khi tạo Lead",
                        "Kiểm tra và xác nhận thông tin thanh toán sau xuất hóa đơn",
                        "Phân tích thị trường và xác định nhu cầu trước khi tạo Cơ hội",
                    ],
                    "question": "Ghép xe VIN vào đơn thực hiện ở giai đoạn nào của luồng bán?",
                },
            ],
            "resources": [
                {
                    "name": "02. Tạo khách hàng tiềm năng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/02. Tạo khách hàng tiềm năng.mp4",
                    "type": "video",
                },
                {
                    "name": "03. Quy luật kiểm tra trùng khi tạo Lead",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/03. Quy luật kiểm tra trùng khi tạo Lead.mp4",
                    "type": "video",
                },
                {
                    "name": "04. Cơ hội bán hàng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/04. Cơ hội bán hàng.mp4",
                    "type": "video",
                },
                {
                    "name": "05. Tạo đơn hàng tổng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/05. Tạo đơn hàng tổng.mp4",
                    "type": "video",
                },
                {
                    "name": "06. Convert đơn hàng tổng với XMĐ",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/06. Convert đơn hàng tổng với XMD.mp4",
                    "type": "video",
                },
                {
                    "name": "07. Battery Option",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/07. Battery Option.mp4",
                    "type": "video",
                },
                {
                    "name": "11. Phát hành đơn hàng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/11. Phát hành đơn hàng.mp4",
                    "type": "video",
                },
                {
                    "name": "12. Ghép xe",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/12. Ghép xe.mp4",
                    "type": "video",
                },
                {
                    "name": "13. Hợp đồng thuê PIN",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/13. Hợp đồng thuê PIN.mp4",
                    "type": "video",
                },
                {
                    "name": "1. Tạo thông tin khách hàng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/02. Tạo khách hàng tiềm năng.mp4",
                    "type": "video",
                },
                {
                    "name": "Demo - Cải tiến Luồng bán XMĐ & Giao diện App XMĐ mới",
                    "path": "KeToan/Demo - Cải tiến Luồng bán XMĐ & Giao diện App XMĐ mới.pptx",
                    "type": "doc",
                },
                {
                    "name": "Tài liệu hướng dẫn luồng cải tiến xe máy điện",
                    "path": "KeToan/Tài liệu hướng dẫn sử dụng luồng cải tiến xe máy điện.docx",
                    "type": "doc",
                },
                {
                    "name": "Video hướng dẫn DMS luồng mới",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/2. Bán hàng/Video hướng dẫn DMS luồng mới.mp4",
                    "type": "video",
                },
                {
                    "name": "VF_HDSD Bán hàng XMĐ thuê Pin trả trước Model MAX",
                    "path": "KeToan/VF _HDSD_Bán hàng XMĐ thuê Pin trả trước Model MAX v0.4_4508.pdf",
                    "type": "doc",
                },
                {
                    "name": "VF_HDSD Thanh lý, chấm dứt, đổi chủ, kích hoạt lại HĐTP",
                    "path": "KeToan/VF_HDSD_Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin.docx",
                    "type": "doc",
                },
                {
                    "name": "Giấy yêu cầu hoàn, chuyển cọc LFP",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/2. Yêu cầu hoàn cọc, chuyển cọc, chuyển sản phẩm.mp4",
                    "type": "doc",
                },
            ],
            "short_title": "Đơn hàng & Hợp đồng Pin",
            "step_type": "task",
            "title": "Tạo Đơn hàng, Ghép xe & Hợp đồng Pin",
        },
        {
            "duration_minutes": 3,
            "goal": "Hoàn tất luồng thu tiền và xuất hóa đơn chuẩn: Tạo Phiếu thu → Áp E-Voucher → Xuất "
            "HĐ GTGT + HĐ Pin → Đẩy VNPT → Giao xe chính thức cho khách.",
            "guides": [
                {
                    "desc": "Tài chính → Phiếu thu → Nhập số tiền đặt cọc/thanh toán → Tạo chi tiết phiếu thu.",
                    "letter": "A",
                    "title": "Tạo Phiếu thu",
                },
                {
                    "desc": "Thêm CTKM / mã E-Voucher vào đúng bước trong đơn hàng, không áp sau khi đã phát hành đơn.",
                    "letter": "B",
                    "title": "Áp chương trình khuyến mãi",
                },
                {
                    "desc": "Xuất HĐ từ DMS → Kiểm tra thông tin khách hàng & MST → Xác nhận.",
                    "letter": "C",
                    "title": "Phát hành Hóa đơn GTGT",
                },
                {
                    "desc": "Chọn HĐ → Đẩy VNPT → Chờ xác nhận từ VNPT → Tải HĐ điện tử về lưu.",
                    "letter": "D",
                    "title": "Đẩy hóa đơn lên VNPT",
                },
                {
                    "desc": "Tạo HĐ dịch vụ thuê Pin → Thực hiện nghiệp vụ Giao xe trên DMS → "
                    "Xác nhận giao xe thành công.",
                    "letter": "E",
                    "title": "Tạo HĐ Pin & Giao xe",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Áp khuyến mãi sau khi phát hành đơn thì hệ thống không tính giảm trừ được nữa.",
                    "id": 1,
                    "options": [
                        "Thực hiện quy trình từng bước trước khi phát hành đơn hàng",
                        "Hoàn tất đẩy hóa đơn và xác nhận thông tin trước",
                        "Nộp hồ sơ Claim với đầy đủ giấy tờ và thông tin",
                        "Thực hiện bất kỳ lúc nào mà không cần quy trình cụ thể",
                    ],
                    "question": "Mã E-Voucher phải được áp vào lúc nào trong quy trình?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Hóa đơn chỉ hợp lệ khi VNPT xác nhận phát hành thành công; "
                    "phải tải bản điện tử về lưu.",
                    "id": 2,
                    "options": [
                        "Chờ VNPT xác nhận, tải hóa đơn điện tử để lưu trữ.",
                        "Xóa hóa đơn DMS mà không kiểm tra tính hợp lệ.",
                        "Tạo phiếu thu mà không xác minh thông tin khách hàng.",
                        "Hủy đơn hàng mà không thông báo hoặc kiểm tra tình trạng.",
                    ],
                    "question": "Sau khi đẩy hóa đơn lên VNPT, bước kế tiếp là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Hóa đơn GTGT bán xe và Hóa đơn dịch vụ thuê Pin là hai chứng từ tách biệt.",
                    "id": 3,
                    "options": [
                        "Tạo hóa đơn Pin để theo dõi và quản lý tài chính",
                        "Gộp tất cả giao dịch thành một hóa đơn duy nhất",
                        "Không cần hóa đơn Pin, có thể dùng chứng từ khác",
                        "Kế toán quyết định phát hành hóa đơn Pin theo quy định",
                    ],
                    "question": "Hóa đơn GTGT và Hóa đơn Pin được tạo riêng hay chung?",
                },
            ],
            "resources": [
                {
                    "name": "08. Tạo Phiếu thu",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/08. Tạo Phiếu thu.mp4",
                    "type": "video",
                },
                {
                    "name": "09. Tạo chi tiết phiếu thu",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/09. Tạo chi tiết phiếu thu.mp4",
                    "type": "video",
                },
                {
                    "name": "10. Thêm chương trình khuyến mãi",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/10. Thêm chương trình khuyến mãi.mp4",
                    "type": "video",
                },
                {
                    "name": "14. Hóa đơn (new)",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/14.Hóa đơn (new).webm",
                    "type": "video",
                },
                {
                    "name": "15. Giao xe (new)",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/15. Giao xe (new).mp4",
                    "type": "video",
                },
                {
                    "name": "16. Đẩy hóa đơn lên VNPT",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/16. Đẩy hóa đơn lên VNPT.mp4",
                    "type": "video",
                },
                {
                    "name": "17. Tạo hóa đơn PIN",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/17. Tạo hóa đơn PIN.mp4",
                    "type": "video",
                },
            ],
            "short_title": "Thu tiền & Hóa đơn",
            "step_type": "task",
            "title": "Thu tiền, Áp KM, Hóa đơn GTGT & Giao xe",
        },
        {
            "duration_minutes": 3,
            "goal": "Lập được đầy đủ bộ hồ sơ Claim NPP chuẩn VinFast: Giấy đề nghị TT NPP + Bảng kê "
            "N677 + Biểu mẫu bổ sung → Nộp trên DMS và track trạng thái phê duyệt.",
            "guides": [
                {
                    "desc": "Claim bù tồn (xe bán từ kho tồn VF) và Claim chiết khấu/hỗ trợ "
                    "(theo chính sách doanh số).",
                    "letter": "A",
                    "title": "Hiểu 2 loại Claim",
                },
                {
                    "desc": "Giấy đề nghị thanh toán NPP + N677 Bảng kê xe chi tiết → Đối "
                    "chiếu với Bảng giá claim ĐLPP 2026.",
                    "letter": "B",
                    "title": "Điền biểu mẫu",
                },
                {
                    "desc": "Theo hướng dẫn thao tác claim trên DMS → Đính kèm biểu mẫu đã ký → Gửi VinFast.",
                    "letter": "C",
                    "title": "Nộp hồ sơ trên DMS",
                },
                {
                    "desc": "Theo dõi trên DMS cho đến khi Claim được phê duyệt và tiền về tài khoản đại lý.",
                    "letter": "D",
                    "title": "Track trạng thái",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Claim bù tồn dành riêng cho xe đại lý bán ra từ nguồn kho tồn của VF.",
                    "id": 1,
                    "options": [
                        "Bán xe từ kho VinFast, đảm bảo chất lượng và tiêu chuẩn kỹ thuật",
                        "Bán tất cả xe trong tháng, bao gồm khuyến mãi và ưu đãi",
                        "Chỉ bán xe trưng bày Demo tại sự kiện và triển lãm",
                        "Xe khách trả lại sẽ được kiểm tra trước khi vào kho lại",
                    ],
                    "question": "Claim bù tồn áp dụng cho loại xe nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Hai biểu mẫu này là bắt buộc, đối chiếu theo Bảng giá claim ĐLPP hiện hành.",
                    "id": 2,
                    "options": [
                        "Giấy đề nghị thanh toán và Bảng kê N677 để hoàn tất thanh toán",
                        "Cung cấp ảnh chụp xe với thông tin đầy đủ để xác nhận",
                        "Gửi email xác nhận với nội dung và thông tin liên lạc rõ ràng",
                        "Chỉ cần thông báo miệng để tiến hành, không cần tài liệu khác",
                    ],
                    "question": "Tài liệu bắt buộc nộp kèm hồ sơ Claim NPP gồm những gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "N677 là bảng kê chi tiết xe làm căn cứ để VF đối soát số tiền phải thanh toán.",
                    "id": 3,
                    "options": [
                        "Liệt kê loại xe và khoản thanh toán cụ thể cho từng xe",
                        "Cập nhật lịch bảo dưỡng cho xe, bao gồm thời gian và dịch vụ",
                        "Thống kê số lượng nhân sự tại đại lý theo vị trí và chức vụ",
                        "Quản lý tình trạng tồn kho phụ tùng, số lượng và loại cần thiết",
                    ],
                    "question": "Bảng kê N677 dùng để làm gì trong hồ sơ Claim?",
                },
            ],
            "resources": [
                {
                    "name": "VF_Hướng dẫn Claim hồ sơ XMĐ",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/1. VF_Hướng dẫn Claim hồ sơ XMĐ.pptx",
                    "type": "doc",
                },
                {
                    "name": "Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ.docx",
                    "type": "doc",
                },
                {
                    "name": "VF_HDSD Luồng claim bù tồn cho XMĐ v1.0",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/VF_HDSD_Luồng claim bù tồn cho XMĐ v1.0.docx",
                    "type": "doc",
                },
                {
                    "name": "Hướng dẫn thao tác luồng hồ sơ claim trên DMS",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ.docx",
                    "type": "doc",
                },
                {
                    "name": "N677 Bảng kê thanh toán chi tiết",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/1. VF_Hướng dẫn Claim hồ sơ XMĐ.pptx",
                    "type": "doc",
                },
                {
                    "name": "Giấy đề nghị thanh toán NPP",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ.docx",
                    "type": "doc",
                },
                {
                    "name": "Bảng giá claim ĐLPP đơn CBNV 2026",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/1. VF_Hướng dẫn Claim hồ sơ XMĐ.pptx",
                    "type": "doc",
                },
                {
                    "name": "Form Bảng kê xe Demo",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/1. VF_Hướng dẫn Claim hồ sơ XMĐ.pptx",
                    "type": "doc",
                },
            ],
            "short_title": "Hồ sơ Claim",
            "step_type": "document",
            "title": "Lập Hồ sơ Claim hoàn tiền với VinFast",
        },
    ],
    "manager": [
        {
            "duration_minutes": 2,
            "goal": "Thấm nhuần tinh thần & sứ mệnh di chuyển xanh của VinGroup. Hiểu vị trí chiến lược của "
            "VinFast XMĐ và vai trò của người Quản lý đại lý trong hệ sinh thái này.",
            "guides": [
                {
                    "desc": "Lịch sử tập đoàn và 5 giá trị cốt lõi: Tín - Tâm - Trí - Tốc - Tinh.",
                    "letter": "A",
                    "title": "VinGroup & Sứ mệnh",
                },
                {
                    "desc": "Vị trí của VinFast trong VinGroup và chiến lược xe điện toàn cầu.",
                    "letter": "B",
                    "title": "VinFast & Di chuyển xanh",
                },
                {
                    "desc": "Dẫn dắt đội ngũ Sale + Kỹ thuật + Kế toán đạt chỉ tiêu KPI doanh số và dịch vụ.",
                    "letter": "C",
                    "title": "Vai trò Manager đại lý XMĐ",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Đây là bộ 5 giá trị cốt lõi xuyên suốt mọi hoạt động của tập đoàn VinGroup.",
                    "id": 1,
                    "options": [
                        "Tín, Tâm, Trí, Tốc, Tinh là giá trị cốt lõi của chúng tôi",
                        "Nhanh, giá rẻ, chất lượng, bền và thẩm mỹ là yếu tố khách hàng cần",
                        "Học hỏi thực tiễn, hiểu sản phẩm, hành động hiệu quả là quy trình của chúng tôi",
                        "Chúng tôi linh hoạt điều chỉnh giá trị theo nhu cầu khách hàng",
                    ],
                    "question": "5 giá trị cốt lõi của VinGroup là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Manager chịu trách nhiệm cả hai trục: doanh số kinh doanh và "
                    "chất lượng dịch vụ sau bán.",
                    "id": 2,
                    "options": [
                        "Đặt chỉ tiêu doanh số và nâng cao chất lượng dịch vụ",
                        "Theo dõi email gửi đi để cải thiện giao tiếp với khách",
                        "Ghi nhận giờ làm thêm để đánh giá hiệu suất và lương",
                        "Phân tích lượt truy cập website để tối ưu trải nghiệm khách",
                    ],
                    "question": "KPI chính mà Manager đại lý XMĐ cần theo dõi là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Ba bộ phận này tạo thành mô hình 3S và đều nằm dưới sự điều phối của Manager.",
                    "id": 3,
                    "options": [
                        "Quản lý Sale, Kỹ thuật, Kế toán để đảm bảo hiệu quả",
                        "Chỉ quản lý bộ phận Sale, không liên quan bộ phận khác",
                        "Chỉ thực hiện nhiệm vụ bộ phận Kỹ thuật, không xem xét khác",
                        "Không quản lý bộ phận nào, không có trách nhiệm gì",
                    ],
                    "question": "Manager đại lý XMĐ trực tiếp dẫn dắt những bộ phận nào?",
                },
            ],
            "resources": [
                {
                    "name": "1. Tài liệu Tự hào VinGroup",
                    "path": "s3://General_doc/TaiLieuChung/1. Tài liệu Tự hào VinGroup.pdf",
                    "type": "doc",
                },
                {
                    "name": "2. Lịch sử & Tổng quan sản phẩm XMĐ",
                    "path": "s3://General_doc/TaiLieuChung/2. Lịch sử & Tổng quan sản phẩm XMĐ_260617.pdf",
                    "type": "doc",
                },
            ],
            "short_title": "Văn hóa VinGroup",
            "step_type": "document",
            "title": "Chào mừng & Văn hóa Doanh nghiệp VinGroup",
        },
        {
            "duration_minutes": 3,
            "goal": "Thuộc lòng Bộ tiêu chuẩn hình ảnh nhận diện Showroom XMĐ (HM55) và tiêu chuẩn vận hành "
            "Xưởng dịch vụ (KD02) chuẩn 3S EV Zone của VinFast.",
            "guides": [
                {
                    "desc": "Bộ nhận diện thương hiệu (biển bảng, màu sắc, font chữ chuẩn VF), "
                    "khu trưng bày xe (vị trí đèn, gương, bục trưng bày), đồng phục nhân "
                    "viên.",
                    "letter": "A",
                    "title": "Tiêu chuẩn HM55 — Showroom",
                },
                {
                    "desc": "Bố trí mặt bằng xưởng, quy trình tiếp nhận → sửa chữa → giao xe, "
                    "tiêu chuẩn an toàn lao động tại xưởng 3S EV Zone.",
                    "letter": "B",
                    "title": "Tiêu chuẩn KD02 — Xưởng dịch vụ",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "HM55 quy định chi tiết vị trí trưng bày, ánh sáng và bục để "
                    "hình ảnh đồng nhất toàn hệ thống.",
                    "id": 1,
                    "options": [
                        "Đặt hàng hóa đúng quy chuẩn về vị trí và ánh sáng để trưng bày hiệu quả.",
                        "Đặt hàng hóa tùy ý, không quan tâm đến quy chuẩn trưng bày.",
                        "Đặt hàng hóa sát tường để tiết kiệm không gian, ảnh hưởng đến tiếp cận.",
                        "Không sử dụng biển bảng chỉ dẫn, tiết kiệm chi phí nhưng khó tìm sản phẩm.",
                    ],
                    "question": "Biển bảng trưng bày xe XMĐ phải đặt ở vị trí như thế nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "KD02 chuẩn hóa cả mặt bằng, luồng công việc và an toàn lao động tại xưởng.",
                    "id": 2,
                    "options": [
                        "Bố trí mặt bằng theo quy trình sửa chữa và giao xe, đảm bảo an toàn",
                        "Chỉ cần một chỗ để xe, không cần quan tâm an toàn hay tiện ích",
                        "Chỉ cần một bàn tiếp khách, không cần chú trọng không gian hay thoải mái",
                        "Không yêu cầu cụ thể về mặt bằng, tùy ý sắp xếp theo ý muốn",
                    ],
                    "question": "Khu vực xưởng dịch vụ KD02 phải có những hạng mục gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Đồng phục nằm trong bộ nhận diện thương hiệu do HM55 quy định.",
                    "id": 3,
                    "options": [
                        "HM55: sản phẩm đặc biệt cho công nghiệp và thương mại.",
                        "KD02: sản phẩm thông dụng cho ứng dụng hàng ngày.",
                        "N677: sản phẩm nâng cao cho dự án công nghệ hiện đại.",
                        "ZVOR: sản phẩm mới với tính năng độc đáo và tương thích.",
                    ],
                    "question": "Bộ tiêu chuẩn nào quy định đồng phục nhân viên showroom?",
                },
            ],
            "resources": [
                {"name": "Đào tạo VF_HM55 cho XMĐ", "path": "s3://KTV/2. Đào tạo VF_HM55 cho XMĐ.pdf", "type": "doc"},
                {
                    "name": "Đào tạo VF_KD02 XMĐ",
                    "path": "Manager/Checklist hướng dẫn setup & nghiệm thu SR – XDV XMĐ 3S EV ZONE.xlsx",
                    "type": "doc",
                },
            ],
            "short_title": "Tiêu chuẩn HM55 & KD02",
            "step_type": "document",
            "title": "Bộ Tiêu chuẩn Vận hành Showroom HM55 & Xưởng KD02",
        },
        {
            "duration_minutes": 3,
            "goal": "Sử dụng thành thạo Bộ Checklist nghiệm thu SR & Xưởng dịch vụ 3S EV Zone — đảm bảo cơ "
            "sở vật chất, biển bảng, trạm sạc và thiết bị xưởng đạt chuẩn VF trước khi khai trương.",
            "guides": [
                {
                    "desc": "Gồm 2 phần — Showroom (SR) và Xưởng dịch vụ (XDV); mỗi hạng mục có "
                    "cột Đạt/Không đạt kèm ghi chú.",
                    "letter": "A",
                    "title": "Hiểu cấu trúc Checklist",
                },
                {
                    "desc": "Đi kiểm tra thực địa theo từng mục → Tick Đạt hoặc ghi nhận lỗi cần khắc phục.",
                    "letter": "B",
                    "title": "Thực hiện nghiệm thu",
                },
                {
                    "desc": "Sau khi toàn bộ Đạt → Submit checklist lên VF để được cấp phép khai trương chính thức.",
                    "letter": "C",
                    "title": "Báo cáo VinFast",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Checklist phải Đạt toàn bộ thì VF mới cấp phép khai trương chính thức.",
                    "id": 1,
                    "options": [
                        "Tất cả hạng mục phải đạt yêu cầu để cấp phép khai trương.",
                        "Có thể khai trương trước, lắp đặt sau để tiết kiệm thời gian.",
                        "Nếu người quản lý cam kết, có thể xem xét cho phép khai trương.",
                        "Quyết định khai trương tùy thuộc vào các yếu tố khác nhau.",
                    ],
                    "question": "Trạm sạc chưa lắp xong có được nghiệm thu khai trương không?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "VF là bên phê duyệt cuối cùng dựa trên checklist nghiệm thu đã hoàn tất.",
                    "id": 2,
                    "options": [
                        "Nộp hồ sơ VinFast để được cấp phép khai trương",
                        "Lưu tài liệu vào tủ hồ sơ đại lý để dễ truy cập",
                        "Gửi tài liệu cho khách hàng để họ tham khảo thông tin",
                        "Không cần nộp tài liệu này cho ai cả",
                    ],
                    "question": "Sau khi checklist hoàn thành, Manager cần nộp cho ai?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Hai khối SR và XDV được nghiệm thu độc lập, mỗi hạng mục có cột Đạt/Không đạt.",
                    "id": 3,
                    "options": [
                        "Chia thành Showroom (SR) và Xưởng dịch vụ (XDV) để quản lý hiệu quả",
                        "Không phân chia khu vực, quản lý trở nên khó khăn hơn",
                        "Có 5 phần khác nhau, mỗi phần có chức năng riêng trong quy trình",
                        "Không chia thành phần, gây thiếu tổ chức và hiệu quả công việc",
                    ],
                    "question": "Checklist nghiệm thu được chia thành mấy phần chính?",
                },
            ],
            "resources": [
                {
                    "name": "Checklist setup & nghiệm thu SR – XDV XMĐ 3S EV ZONE",
                    "path": "Manager/Checklist hướng dẫn setup & nghiệm thu SR – XDV XMĐ 3S EV ZONE.xlsx",
                    "type": "doc",
                }
            ],
            "short_title": "Checklist Nghiệm thu",
            "step_type": "task",
            "title": "Checklist Setup Cơ sở vật chất & Nghiệm thu Đại lý 3S",
        },
        {
            "duration_minutes": 2,
            "goal": "Áp dụng Bộ tiêu chuẩn chất lượng dịch vụ XMĐ trong quản lý vận hành hàng ngày. Biết "
            "tiếp nhận, phân loại và escalate khiếu nại đến đúng đầu mối VinFast. Biết dùng DMS tra "
            "cứu tài liệu nội bộ.",
            "guides": [
                {
                    "desc": "KPI NPS (Net Promoter Score), thời gian tiếp nhận xe, thời gian giao "
                    "xe và mức độ hài lòng của khách.",
                    "letter": "A",
                    "title": "Tiêu chuẩn CLDV hàng ngày",
                },
                {
                    "desc": "Lắng nghe → Ghi nhận → Phân loại (kỹ thuật / thương mại / chất lượng sản phẩm).",
                    "letter": "B",
                    "title": "Tiếp nhận khiếu nại",
                },
                {
                    "desc": "Tra danh sách đầu mối VF theo từng loại khiếu nại → Escalate trong SLA quy định.",
                    "letter": "C",
                    "title": "Escalation đúng đầu mối",
                },
                {
                    "desc": "Đăng nhập → Tra cứu tài liệu nội bộ VF mới nhất để cập nhật cho đội ngũ.",
                    "letter": "D",
                    "title": "Kho tài liệu DMS",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Danh sách đầu mối DVTP phân loại theo mảng, giúp chuyển đúng người và đúng SLA.",
                    "id": 1,
                    "options": [
                        "Đầu mối kỹ thuật chính xử lý khiếu nại dịch vụ khách hàng hiệu quả",
                        "Nhân viên đại lý tham gia xử lý khiếu nại không cần phân công",
                        "Gửi thông tin khiếu nại cho khách hàng khác mà không kiểm tra",
                        "Không thực hiện quy trình escalate, tự quyết giải quyết tại chỗ",
                    ],
                    "question": "Khách khiếu nại lỗi kỹ thuật xe thì escalate đến đầu mối nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Tiêu chuẩn dịch vụ XMĐ đặt ngưỡng NPS cụ thể làm mốc cảnh báo cho đại lý.",
                    "id": 2,
                    "options": [
                        "Khắc phục ngay khi doanh thu dưới ngưỡng Tiêu chuẩn dịch vụ XMĐ.",
                        "Chỉ số NPS không quan trọng cho sự phát triển ngắn hạn.",
                        "Chỉ xem xét quy trình khi khách hàng kiện ra tòa.",
                        "Phân tích nguyên nhân và điều chỉnh chiến lược khi doanh số giảm.",
                    ],
                    "question": "KPI NPS dưới mức nào thì cần họp bàn cải thiện ngay?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Lắng nghe và ghi nhận trước rồi mới phân loại, đó là bước bắt "
                    "buộc để escalate đúng.",
                    "id": 3,
                    "options": [
                        "Lắng nghe và ghi nhận chi tiết khiếu nại từ khách hàng",
                        "Phản bác ngay mà không xem xét tình huống kỹ lưỡng",
                        "Chuyển máy cho người khác mà không thông báo rõ ràng",
                        "Hứa bồi thường ngay mà không xem xét điều khoản liên quan",
                    ],
                    "question": "Bước đầu tiên khi tiếp nhận một khiếu nại của khách là gì?",
                },
            ],
            "resources": [
                {
                    "name": "Tiêu chuẩn dịch vụ XMĐ",
                    "path": "s3://Sale/3.1 Tiêu chuẩn dịch vụ XMĐ_251121.pdf",
                    "type": "doc",
                },
                {
                    "name": "Danh sách đầu mối xử lý khiếu nại DVTP",
                    "path": "s3://Sale/3.1 Tiêu chuẩn dịch vụ XMĐ_251121.pdf",
                    "type": "doc",
                },
                {
                    "name": "HDSD tìm kiếm và sử dụng Kho tài liệu DMS",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/250717_HDSD tim kiem va su dung Kho tai lieu DMS.pdf",
                    "type": "doc",
                },
                {
                    "name": "01. Hướng dẫn đăng nhập DMS",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/01. Hướng dẫn đăng nhập DMS.mp4",
                    "type": "video",
                },
            ],
            "short_title": "Chất lượng & Khiếu nại",
            "step_type": "document",
            "title": "Tiêu chuẩn Chất lượng Dịch vụ & Quản lý Khiếu nại",
        },
        {
            "duration_minutes": 2,
            "goal": "Nắm toàn bộ ưu đãi hiện hành & chương trình Chăm sóc xe miễn phí để chỉ đạo đội ngũ "
            "Sale - Kỹ thuật truyền thông thống nhất, và trả lời chính xác khi khách hỏi trực tiếp.",
            "guides": [
                {
                    "desc": "E-Voucher, quà tặng kèm, ưu đãi CBNV — kèm thời hạn áp dụng của từng chương trình.",
                    "letter": "A",
                    "title": "Nắm danh mục ưu đãi hiện hành",
                },
                {
                    "desc": "Sale thông báo ưu đãi, Kế toán mới là người nhập E-Voucher vào DMS — "
                    "tránh để nhân viên hứa sai với khách.",
                    "letter": "B",
                    "title": "Thống nhất thông điệp cho đội ngũ",
                },
                {
                    "desc": "Nắm nội dung chương trình để chỉ đạo xưởng tiếp nhận và hướng dẫn "
                    "khách đăng ký đúng quy trình.",
                    "letter": "C",
                    "title": "Chăm sóc xe miễn phí",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Manager là người bảo đảm Sale và Kỹ thuật nói cùng một thông điệp với khách hàng.",
                    "id": 1,
                    "options": [
                        "Chỉ đạo truyền thông thống nhất, trả lời khách hàng chính xác, hiệu quả.",
                        "Phát triển chương trình riêng mà không cần sự đồng ý từ cấp trên.",
                        "Giữ bí mật thông tin để bảo vệ chiến lược công ty khỏi rò rỉ.",
                        "Không sử dụng vào mục đích nào và có thể bỏ qua trong quy trình.",
                    ],
                    "question": "Manager cần nắm chương trình khuyến mãi để làm gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Chương trình chỉ bao gồm các hạng mục chăm sóc cơ bản theo định kỳ.",
                    "id": 2,
                    "options": [
                        "Kiểm tra xe định kỳ, bơm lốp và vệ sinh miễn phí cho khách",
                        "Thay pin miễn phí cho xe trong bảo hành, đảm bảo hiệu suất",
                        "Đổi xe mới miễn phí sau 1 năm sử dụng, nâng cao trải nghiệm",
                        "Sửa chữa hư hỏng miễn phí, thay linh kiện và bảo trì định kỳ",
                    ],
                    "question": "Chương trình chăm sóc xe miễn phí gồm những dịch vụ gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Phân quyền thống nhất toàn hệ thống: chỉ Kế toán thao tác nhập E-Voucher trên DMS.",
                    "id": 3,
                    "options": [
                        "Thực hiện công việc kế toán, ghi chép, lập báo cáo và quản lý ngân sách.",
                        "Tư vấn, hỗ trợ khách hàng mua sắm và cung cấp thông tin sản phẩm.",
                        "Thực hiện nhiệm vụ kỹ thuật, kiểm tra, bảo trì và sửa chữa thiết bị.",
                        "Quản lý showroom, sắp xếp trưng bày, tổ chức sự kiện và giám sát nhân viên.",
                    ],
                    "question": "Ai là người nhập mã E-Voucher vào hệ thống DMS?",
                },
            ],
            "resources": [
                {
                    "name": "Đào tạo Chương trình chăm sóc xe miễn phí",
                    "path": "s3://General_doc/CTKM/Đào tạo Chương trình chăm sóc xe miễn phí_0043.pptx",
                    "type": "doc",
                },
                {
                    "name": "VF_HDSD Chương trình chăm sóc xe miễn phí",
                    "path": "KTV/VF_HDSD_HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0_7748.docx",
                    "type": "doc",
                },
            ],
            "short_title": "Khuyến mãi & Chăm sóc xe",
            "step_type": "document",
            "title": "Chương trình Khuyến mãi & Chăm sóc Xe miễn phí",
        },
    ],
    "owner": [
        {
            "duration_minutes": 4,
            "goal": "Nắm định hướng hệ sinh thái VinFast và tiêu chuẩn dịch vụ mà Đại lý 3S cam kết với khách hàng.",
            "guides": [
                {
                    "desc": "Thúc đẩy chuyển đổi giao thông xanh toàn diện với hạ tầng trạm sạc phủ rộng.",
                    "letter": "A",
                    "title": "Tầm nhìn Xanh VinFast",
                },
                {
                    "desc": "Hưởng hoa hồng bán xe, chiết khấu phụ tùng, doanh thu dịch vụ & hoa hồng sạc pin.",
                    "letter": "B",
                    "title": "Quyền lợi Đại lý 3S",
                },
                {
                    "desc": "Đại lý chịu trách nhiệm duy trì tiêu chuẩn dịch vụ XMĐ trên toàn bộ "
                    "hành trình khách hàng.",
                    "letter": "C",
                    "title": "Cam kết chất lượng dịch vụ",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "3S đại diện cho Bán hàng (Sales), Dịch vụ sửa chữa (Service) và "
                    "Phụ tùng chính hãng (Spare parts).",
                    "id": 1,
                    "options": [
                        "Quản lý bán hàng, dịch vụ khách hàng và cung cấp phụ tùng",
                        "Chỉ bán hàng, không hỗ trợ dịch vụ khách hàng",
                        "Chỉ bảo hành sản phẩm, không sửa chữa hay bảo trì",
                        "Chỉ cho thuê xe, không có lựa chọn dịch vụ khác",
                    ],
                    "question": "Mô hình Đại lý 3S VinFast bao gồm 3 chức năng chính nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "VF đồng hành toàn diện cùng Đại lý từ hạ tầng phần mềm, đào tạo "
                    "nhân sự đến chính sách bán hàng.",
                    "id": 2,
                    "options": [
                        "Truyền thông thương hiệu, đào tạo nhân sự, sử dụng DMS và chiết khấu hợp lý",
                        "Không hỗ trợ khách hàng trong giao dịch và dịch vụ",
                        "Giao xe cho khách mà không hướng dẫn hay thông tin bổ sung",
                        "Đại lý tự thực hiện quy trình mà không hỗ trợ từ công ty",
                    ],
                    "question": "Nhà máy VinFast hỗ trợ Đại lý ủy quyền ở những khía cạnh nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "VF ban hành tiêu chuẩn, còn đại lý là bên trực tiếp cam kết và "
                    "thực thi với khách hàng.",
                    "id": 3,
                    "options": [
                        "Đại lý hỗ trợ khách hàng từ tiếp cận đến sử dụng sản phẩm",
                        "Chỉ nhà máy VinFast tham gia sản xuất và cung cấp dịch vụ",
                        "Chỉ nhân viên kỹ thuật chuyên môn cao thực hiện công việc sản phẩm",
                        "Không ai chịu trách nhiệm giải quyết vấn đề dịch vụ khách hàng",
                    ],
                    "question": "Ai chịu trách nhiệm duy trì tiêu chuẩn dịch vụ XMĐ tại điểm bán?",
                },
            ],
            "resources": [
                {
                    "name": "1. Tài liệu Tự hào VinGroup",
                    "path": "s3://General_doc/TaiLieuChung/1. Tài liệu Tự hào VinGroup.pdf",
                    "type": "doc",
                },
                {
                    "name": "2. Lịch sử & Tổng quan sản phẩm XMĐ",
                    "path": "s3://General_doc/TaiLieuChung/2. Lịch sử & Tổng quan sản phẩm XMĐ_260617.pdf",
                    "type": "doc",
                },
            ],
            "short_title": "Định hướng Chiến lược",
            "step_type": "document",
            "title": "Chào mừng & Định hướng Chiến lược Cửa hàng 3S VF",
        },
        {
            "duration_minutes": 5,
            "goal": "Thạo các bước nghiệm thu mặt bằng Showroom 3S và tiêu chuẩn trưng bày HM55 của VF.",
            "guides": [
                {
                    "desc": "Kiểm tra logo VinFast, biển bảng chuẩn bộ nhận diện thương hiệu.",
                    "letter": "A",
                    "title": "Checklist nhận diện mặt tiền",
                },
                {
                    "desc": "Chạy qua toàn bộ Checklist setup & nghiệm thu SR – XDV XMĐ 3S EV ZONE.",
                    "letter": "B",
                    "title": "Nghiệm thu SR – XDV",
                },
                {
                    "desc": "Bảo đảm bố trí trưng bày, ánh sáng, khu tiếp khách đúng chuẩn HM55.",
                    "letter": "C",
                    "title": "Đối chiếu tiêu chuẩn HM55",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Biên bản nghiệm thu chính thức chứng nhận Đại lý đạt đầy đủ các "
                    "tiêu chuẩn hình ảnh và an toàn của VF.",
                    "id": 1,
                    "options": [
                        "Ký biên bản nghiệm thu 3S giữa Đại lý và VinFast để xác nhận chất lượng",
                        "Không nghiệm thu có thể ảnh hưởng đến chất lượng sản phẩm và dịch vụ",
                        "Chụp ảnh không đủ để đảm bảo tiêu chuẩn nghiệm thu cần thiết",
                        "Gửi tin nhắn thông báo nhưng không có xác nhận chính thức từ đại lý",
                    ],
                    "question": "Hồ sơ bắt buộc phải hoàn tất trước khi Showroom chính thức khai trương là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "HM55 là bộ tiêu chuẩn vận hành và trưng bày hình ảnh dành cho không gian Showroom.",
                    "id": 2,
                    "options": [
                        "HM55: sản phẩm đa năng, hiệu quả cho nhiều lĩnh vực.",
                        "N677: sản phẩm cơ bản, dùng cho ứng dụng đơn giản.",
                        "ZVOR: thiết kế độc đáo nhưng hiệu suất kém.",
                        "KD02: sử dụng trong tình huống nhất định, không chuyên nghiệp.",
                    ],
                    "question": "Bộ tiêu chuẩn nào quy định cách trưng bày xe và bố trí không gian Showroom?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Nhận diện đồng nhất trên toàn hệ thống là điều kiện bắt buộc để được nghiệm thu.",
                    "id": 3,
                    "options": [
                        "Tuân thủ quy định bộ nhận diện thương hiệu VinFast để đảm bảo nhất quán.",
                        "Thiết kế biển hiệu theo sở thích cá nhân mà không cần quy chuẩn.",
                        "Sử dụng lại biển hiệu cũ mà không thay đổi để tiết kiệm chi phí.",
                        "Không lắp đặt biển hiệu, chỉ quảng bá qua các kênh truyền thông khác.",
                    ],
                    "question": "Hạng mục nhận diện mặt tiền showroom cần đạt yêu cầu gì?",
                },
            ],
            "resources": [
                {
                    "name": "Checklist setup & nghiệm thu SR – XDV XMĐ 3S EV ZONE",
                    "path": "Manager/Checklist hướng dẫn setup & nghiệm thu SR – XDV XMĐ 3S EV ZONE.xlsx",
                    "type": "doc",
                },
                {"name": "Đào tạo VF_HM55 cho XMĐ", "path": "s3://KTV/2. Đào tạo VF_HM55 cho XMĐ.pdf", "type": "doc"},
            ],
            "short_title": "Setup & Nghiệm thu",
            "step_type": "task",
            "title": "Checklist Setup Showroom & Nghiệm thu Tiêu chuẩn VF",
        },
        {
            "duration_minutes": 5,
            "goal": "Biết cách cấp tài khoản DMS, phân quyền theo vai trò và kiểm soát truy cập dữ liệu đại lý.",
            "guides": [
                {
                    "desc": "Vào Phân hệ Quản trị → Nhập email nhân viên → Chọn Role tương ứng (Kế "
                    "toán, Sales, Kỹ thuật).",
                    "letter": "A",
                    "title": "Mời nhân viên mới",
                },
                {
                    "desc": "Đảm bảo chỉ Kế toán mới có quyền duyệt hóa đơn GTGT & chỉ Manager có "
                    "quyền xem tổng báo cáo.",
                    "letter": "B",
                    "title": "Giám sát quyền truy cập",
                },
                {
                    "desc": "Khóa tài khoản kịp thời để bảo đảm an toàn dữ liệu kinh doanh.",
                    "letter": "C",
                    "title": "Thu hồi quyền khi nhân sự nghỉ",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Chủ Đại lý (Owner) giữ quyền Admin cao nhất để khởi tạo và phân "
                    "quyền cho nhân sự dưới quyền.",
                    "id": 1,
                    "options": [
                        "Quản lý hoạt động và điều hành hệ thống đại lý",
                        "Bảo vệ an ninh, giám sát khu vực và hỗ trợ khách",
                        "Khách hàng yêu cầu thông tin sản phẩm và dịch vụ",
                        "Đối tác giao hàng phối hợp với đại lý để giao nhận",
                    ],
                    "question": "Ai là người có thẩm quyền cao nhất để phân quyền và cấp tài khoản "
                    "DMS cho nhân viên Đại lý?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Khóa tài khoản lập tức ngăn ngừa nguy cơ rò rỉ dữ liệu khách hàng "
                    "và công nợ đại lý.",
                    "id": 2,
                    "options": [
                        "Khóa ngay tài khoản DMS để bảo vệ thông tin.",
                        "Không thay đổi tài khoản để tránh gián đoạn.",
                        "Chuyển nhượng tài khoản mà không xem xét quy định.",
                        "Đổi tên nhân viên mà không cần xác nhận quản lý.",
                    ],
                    "question": "Hành động bắt buộc khi có nhân sự nghỉ việc tại đại lý để bảo vệ dữ "
                    "liệu kinh doanh là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Cấp quyền tối thiểu giới hạn thiệt hại nếu một tài khoản bị lộ hoặc thao tác nhầm.",
                    "id": 3,
                    "options": [
                        "Cấp quyền tối thiểu cần thiết cho từng cá nhân",
                        "Cấp quyền quản trị cho mọi nhân viên",
                        "Sử dụng chung tài khoản cho toàn phòng",
                        "Cấp quyền theo thâm niên để khuyến khích phát triển",
                    ],
                    "question": "Nguyên tắc đúng khi cấp quyền tài khoản DMS cho nhân viên là gì?",
                },
            ],
            "resources": [
                {
                    "name": "01. Hướng dẫn đăng nhập DMS",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/01. Hướng dẫn đăng nhập DMS.mp4",
                    "type": "video",
                },
                {
                    "name": "HDSD tìm kiếm và sử dụng Kho tài liệu DMS",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/250717_HDSD tim kiem va su dung Kho tai lieu DMS.pdf",
                    "type": "doc",
                },
            ],
            "short_title": "Phân quyền DMS",
            "step_type": "task",
            "title": "Phân quyền Quản trị & Mời Nhân viên vào DMS",
        },
        {
            "duration_minutes": 5,
            "goal": "Kiểm soát dòng tiền, nắm bảng giá claim và phê duyệt hồ sơ Claim hoàn tiền gửi VF.",
            "guides": [
                {
                    "desc": "Hiểu toàn bộ quy trình Claim của đại lý để kiểm soát tiến độ thu hồi tiền.",
                    "letter": "A",
                    "title": "Nắm luồng hồ sơ Claim",
                },
                {
                    "desc": "So khớp số tiền đề nghị với Bảng giá claim ĐLPP do VF ban hành.",
                    "letter": "B",
                    "title": "Đối chiếu bảng giá claim",
                },
                {
                    "desc": "Phê duyệt bảng kê và giấy đề nghị thanh toán trước khi gửi về VF.",
                    "letter": "C",
                    "title": "Duyệt hồ sơ trước khi nộp",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Đại lý 3S tối ưu lợi nhuận từ đa nguồn: Bán xe mới, Phụ tùng, "
                    "Dịch vụ sửa chữa và dịch vụ trạm sạc.",
                    "id": 1,
                    "options": [
                        "Hoa hồng từ bán xe, phụ tùng, dịch vụ sửa chữa và sạc pin",
                        "Chỉ bán xe, không kèm dịch vụ bảo trì hay sửa chữa",
                        "Chỉ rửa xe, không bao gồm bảo trì hay sửa chữa",
                        "Chỉ nhận thưởng cuối quý, không có thu nhập từ doanh thu",
                    ],
                    "question": "Khoản thu nhập nào đóng góp vào cơ cấu lợi nhuận của Đại lý 3S VinFast?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Bảng giá claim ĐLPP là căn cứ duy nhất để VF đối soát và giải ngân cho đại lý.",
                    "id": 2,
                    "options": [
                        "Bảng giá claim ĐLPP chính thức từ VF, đảm bảo minh bạch và công bằng",
                        "Giá đại lý tự định, thay đổi theo thời điểm, không theo quy định",
                        "Giá thị trường tự do dao động mạnh, phụ thuộc cung cầu và xu hướng",
                        "Không cần căn cứ, dễ dẫn đến không nhất quán và thiếu minh bạch",
                    ],
                    "question": "Căn cứ nào để đối chiếu số tiền đề nghị trong hồ sơ Claim?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Mỗi lần hồ sơ bị trả lại là thêm một chu kỳ 5-7 ngày làm việc, "
                    "ảnh hưởng trực tiếp dòng tiền.",
                    "id": 3,
                    "options": [
                        "Hồ sơ sai sẽ bị trả lại, làm chậm thu hồi tiền",
                        "Có thể gia hạn nộp hồ sơ bằng yêu cầu chính thức",
                        "Công ty VF cho phép nộp hồ sơ muộn trong trường hợp đặc biệt",
                        "Không nộp hồ sơ có thể gây rắc rối không cần thiết",
                    ],
                    "question": "Vì sao chủ đại lý cần duyệt hồ sơ Claim trước khi nộp về VF?",
                },
            ],
            "resources": [
                {
                    "name": "VF_Hướng dẫn Claim hồ sơ XMĐ",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/1. VF_Hướng dẫn Claim hồ sơ XMĐ.pptx",
                    "type": "doc",
                },
                {
                    "name": "Bảng giá claim ĐLPP đơn CBNV 2026",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/1. VF_Hướng dẫn Claim hồ sơ XMĐ.pptx",
                    "type": "doc",
                },
                {
                    "name": "Giấy đề nghị thanh toán NPP",
                    "path": "s3://KeToan/Hướng dẫn hồ sơ claim xe máy điện/Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ.docx",
                    "type": "doc",
                },
            ],
            "short_title": "Dòng tiền & Claim",
            "step_type": "document",
            "title": "Quản lý Dòng tiền, Chiết khấu & Hồ sơ Claim Tổng",
        },
    ],
    "sale": [
        {
            "duration_minutes": 2,
            "goal": "Truyền lửa tự hào về thương hiệu VinFast và nắm vững thông số kỹ thuật, USP của từng dòng "
            "xe XMĐ để tư vấn tự tin.",
            "guides": [
                {
                    "desc": "Sứ mệnh, lịch sử và vị trí chiến lược của VinFast trong hệ sinh thái VinGroup.",
                    "letter": "A",
                    "title": "VinFast & Di chuyển xanh",
                },
                {
                    "desc": "Klara S / Feliz S / Vento S / Evo200 / VF Evo — thông số, màu sắc, giá tham khảo.",
                    "letter": "B",
                    "title": "Danh mục xe XMĐ",
                },
                {
                    "desc": "An toàn hơn, tuổi thọ dài hơn so với pin lithium thường — lý do khách chọn VF.",
                    "letter": "C",
                    "title": "Điểm khác biệt Pin LFP",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Klara S và Feliz S định vị cho nhu cầu di chuyển nội đô, ưu tiên "
                    "sự nhẹ nhàng và tiện dụng.",
                    "id": 1,
                    "options": [
                        "Xe máy điện nhỏ gọn, dễ lái, tiết kiệm năng lượng cho đô thị",
                        "Xe tải điện lớn, bền bỉ, chuyên chở hàng hóa nặng hiệu quả",
                        "Ô tô điện 7 chỗ, rộng rãi, an toàn cho gia đình di chuyển",
                        "Xe máy xăng mạnh mẽ, thích hợp cho chuyến đi dài, tốn nhiên liệu",
                    ],
                    "question": "Dòng xe nào phù hợp cho khách hàng nữ, đi nội đô ngắn?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Pin LFP ổn định nhiệt tốt hơn, ít nguy cơ cháy nổ và có số chu kỳ sạc cao hơn.",
                    "id": 2,
                    "options": [
                        "Sản phẩm an toàn hơn và bền hơn so với thị trường",
                        "Sản phẩm nhẹ nhưng dễ hỏng hơn các sản phẩm khác",
                        "Giá rẻ nhưng tiềm ẩn rủi ro an toàn cho người dùng",
                        "Sản phẩm không có ưu điểm nổi bật so với đối thủ",
                    ],
                    "question": "Ưu điểm vượt trội của Pin LFP so với pin thường là gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Di chuyển xanh là định hướng chiến lược xuyên suốt của VinFast "
                    "trong hệ sinh thái VinGroup.",
                    "id": 3,
                    "options": [
                        "Phát triển giải pháp giao thông xanh bền vững để giảm ô nhiễm",
                        "Tăng doanh số xe xăng qua khuyến mãi hấp dẫn",
                        "Phục vụ và phát triển thị trường xuất khẩu xe máy",
                        "Cung cấp phụ tùng giá rẻ để thu hút khách hàng",
                    ],
                    "question": "Sứ mệnh mà VinFast theo đuổi với dòng xe máy điện là gì?",
                },
            ],
            "resources": [
                {
                    "name": "1. Tài liệu Tự hào VinGroup",
                    "path": "s3://General_doc/TaiLieuChung/1. Tài liệu Tự hào VinGroup.pdf",
                    "type": "doc",
                },
                {
                    "name": "2. Lịch sử & Tổng quan sản phẩm XMĐ",
                    "path": "s3://General_doc/TaiLieuChung/2. Lịch sử & Tổng quan sản phẩm XMĐ_260617.pdf",
                    "type": "doc",
                },
            ],
            "short_title": "Tổng quan Sản phẩm",
            "step_type": "document",
            "title": "Chào mừng & Tổng quan Sản phẩm XMĐ VinFast",
        },
        {
            "duration_minutes": 3,
            "goal": "Thuần thục 7 bước bán hàng chuẩn VinFast từ đón tiếp đến chăm sóc sau bán, tăng tỷ lệ "
            "chốt đơn hiệu quả.",
            "guides": [
                {
                    "desc": "Greeting — tạo ấn tượng đầu tiên chuyên nghiệp, thân thiện.",
                    "letter": "1",
                    "title": "Đón tiếp & Xây dựng thiện cảm",
                },
                {
                    "desc": "Need Discovery — hỏi đúng để hiểu nhu cầu di chuyển thực tế của khách.",
                    "letter": "2",
                    "title": "Khai thác nhu cầu",
                },
                {
                    "desc": "Product Presentation — trình bày đúng USP của mẫu xe phù hợp.",
                    "letter": "3",
                    "title": "Giới thiệu xe & Demo tính năng",
                },
                {
                    "desc": "Test Ride — để khách trực tiếp cảm nhận khả năng vận hành.",
                    "letter": "4",
                    "title": "Tổ chức Lái thử",
                },
                {
                    "desc": "Handling Objections — giải tỏa lo ngại về pin, chi phí, bảo hành.",
                    "letter": "5",
                    "title": "Tư vấn gói Pin & Xử lý từ chối",
                },
                {
                    "desc": "Closing — chốt đơn và bàn giao hồ sơ sang Kế toán.",
                    "letter": "6",
                    "title": "Chốt cọc & Hướng dẫn ký hợp đồng",
                },
                {
                    "desc": "After-Sales — giữ quan hệ để có nguồn khách giới thiệu.",
                    "letter": "7",
                    "title": "Chăm sóc sau bán & Giới thiệu khách mới",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Đây là tình huống xử lý từ chối kinh điển: đưa dữ liệu về công "
                    "nghệ LFP và cam kết bảo hành thay vì né tránh.",
                    "id": 1,
                    "options": [
                        "Giải thích sự khác biệt giữa pin LFP và pin điện thoại, cùng chính sách bảo hành",
                        "Đồng ý về pin nhưng không cung cấp thông tin chi tiết",
                        "Tránh trả lời về pin, chuyển sang chủ đề khác",
                        "Hứa đổi pin miễn phí bất cứ lúc nào không cần điều kiện",
                    ],
                    "question": "Khách nói 'Pin điện thoại còn hao huống gì pin xe' — xử lý thế nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Khai thác nhu cầu sai dẫn tới toàn bộ phần tư vấn phía sau lệch "
                    "hướng và khách rời đi.",
                    "id": 2,
                    "options": [
                        "Khai thác nhu cầu khách hàng để giới thiệu xe phù hợp",
                        "Chăm sóc khách hàng sau bán, theo dõi sự hài lòng",
                        "Đón tiếp khách hàng chuyên nghiệp, cung cấp thông tin cần thiết",
                        "Ký hợp đồng rõ ràng, đảm bảo điều khoản minh bạch",
                    ],
                    "question": "Bước nào trong 7 bước dễ mất khách nhất nếu làm sai?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Thứ tự: Đón tiếp → Khai thác nhu cầu → Giới thiệu xe → Lái thử → "
                    "Xử lý từ chối → Chốt cọc → Sau bán.",
                    "id": 3,
                    "options": [
                        "Tổ chức Lái thử cho khách hàng để nâng cao sự hài lòng",
                        "Chốt cọc sau khi tư vấn đầy đủ thông tin sản phẩm",
                        "Đón tiếp khách tại showroom, hướng dẫn tham quan sản phẩm",
                        "Chăm sóc khách hàng sau bán, theo dõi phản hồi và bảo trì",
                    ],
                    "question": "Bước thứ 4 trong quy trình bán hàng 7 bước chuẩn VF là gì?",
                },
            ],
            "resources": [
                {
                    "name": "Tài liệu Quy trình và Kỹ năng bán hàng XMĐ",
                    "path": "s3://Sale/4. Tài liệu Quy trình và Kỹ năng bán hàng XMĐ.pdf",
                    "type": "doc",
                }
            ],
            "short_title": "Bán hàng 7 bước",
            "step_type": "document",
            "title": "Quy trình & Kỹ năng Bán hàng 7 bước XMĐ",
        },
        {
            "duration_minutes": 3,
            "goal": "Nắm vững chính sách bán hàng XMĐ mới nhất. So sánh và tư vấn chính xác gói Pin: Thuê trả "
            "trước Model MAX so với Mua đứt Pin, phù hợp nhu cầu và túi tiền từng khách.",
            "guides": [
                {
                    "desc": "Nắm rõ giá niêm yết mới nhất của từng dòng xe (Klara S / Feliz S / Vento S...).",
                    "letter": "A",
                    "title": "Bảng giá xe & cấu hình",
                },
                {
                    "desc": "Thuê pin LFP: phí cố định, VF bảo trì pin, hợp khách đi nhiều. Mua đứt "
                    "pin: trả một lần, tự chịu chi phí bảo dưỡng.",
                    "letter": "B",
                    "title": "So sánh 2 gói Pin",
                },
                {
                    "desc": "Giải thích rõ cho khách trước khi ký — TVBH không thao tác trên DMS, Kế "
                    "toán mới thực hiện.",
                    "letter": "C",
                    "title": "Điều kiện hoàn cọc / chuyển cọc",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Có quy trình chấm dứt HĐTP rõ ràng; TVBH giải thích còn Kế toán "
                    "thực hiện trên DMS.",
                    "id": 1,
                    "options": [
                        "Giải thích thủ tục chấm dứt hợp đồng và hoàn cọc theo quy định",
                        "Khẳng định dừng hợp đồng là không thể trong mọi trường hợp",
                        "Cam kết hoàn trả tiền ngay sau khi hoàn tất thủ tục",
                        "Khuyến khích khách tự liên hệ nhà máy để giải quyết vấn đề",
                    ],
                    "question": "Khách hỏi thuê pin mà không dùng nữa thì sao — tư vấn thế nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Chỉ bảng giá trong chính sách bán hàng bản mới nhất do VF ban hành "
                    "mới có giá trị áp dụng.",
                    "id": 2,
                    "options": [
                        "Bảng giá chi tiết trong Chính sách bán hàng XMĐ mới nhất của VF",
                        "Giá thỏa thuận riêng, thay đổi theo từng trường hợp cụ thể",
                        "Giá tham khảo trên mạng xã hội, không phản ánh giá thực tế",
                        "Giá của đại lý khác, khác biệt do chính sách kinh doanh riêng",
                    ],
                    "question": "Giá xe Klara S theo gói thuê Pin được căn cứ vào đâu?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Khách đi nhiều thì pin hao nhanh; gói thuê chuyển rủi ro chai pin sang VF.",
                    "id": 3,
                    "options": [
                        "Gói thuê pin — VF bảo trì, thay thế pin chai để tối ưu hiệu suất.",
                        "Mua đứt pin mà không xem xét gói thuê pin tiết kiệm hơn.",
                        "Không mua pin, không có nguồn pin dự phòng cho thiết bị.",
                        "Quyết định mua pin mà không tham khảo ý kiến chuyên gia hỗ trợ.",
                    ],
                    "question": "Khách đi lại nhiều mỗi ngày nên được tư vấn gói pin nào?",
                },
            ],
            "resources": [
                {
                    "name": "Chính sách bán hàng XMĐ",
                    "path": "s3://General_doc/CTKM/260801_Chính sách bán hàng_XMĐ.pdf",
                    "type": "doc",
                }
            ],
            "short_title": "Chính sách & Gói Pin",
            "step_type": "document",
            "title": "Chính sách Bán hàng & Tư vấn Gói Pin LFP",
        },
        {
            "duration_minutes": 2,
            "goal": "Nắm toàn bộ chương trình khuyến mãi & ưu đãi hiện hành để dùng đúng lúc, tăng tỷ lệ chốt "
            "cọc. Biết giới thiệu chương trình Chăm sóc xe miễn phí cho khách sau bán.",
            "guides": [
                {
                    "desc": "E-Voucher giảm giá / Quà tặng kèm / Ưu đãi CBNV — nắm thời hạn áp dụng "
                    "để tư vấn đúng. TVBH chỉ THÔNG BÁO ưu đãi, Kế toán mới NHẬP E-Voucher "
                    "vào DMS.",
                    "letter": "A",
                    "title": "Các ưu đãi hiện hành",
                },
                {
                    "desc": "Giới thiệu chương trình bảo dưỡng định kỳ miễn phí — lợi ích quan trọng khi mua xe VF.",
                    "letter": "B",
                    "title": "Chăm sóc xe miễn phí",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "TVBH thông báo ưu đãi cho khách, còn thao tác nhập E-Voucher trên "
                    "DMS thuộc về Kế toán.",
                    "id": 1,
                    "options": [
                        "Thực hiện công việc kế toán: ghi chép, báo cáo tài chính, quản lý thu chi",
                        "Cung cấp dịch vụ tư vấn bán hàng và hỗ trợ khách hàng chọn sản phẩm",
                        "Khách hàng tự nhập thông tin nhưng phải tuân thủ quy trình chính xác",
                        "Kỹ thuật viên bảo trì, sửa chữa và kiểm tra thiết bị đảm bảo an toàn",
                    ],
                    "question": "Ai là người nhập mã E-Voucher vào hệ thống DMS?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Chương trình tập trung vào bảo dưỡng định kỳ cơ bản, không bao gồm "
                    "thay thế linh kiện lớn.",
                    "id": 2,
                    "options": [
                        "Kiểm tra xe định kỳ, bơm lốp và vệ sinh miễn phí theo lịch",
                        "Thay pin mới miễn phí không giới hạn trong thời gian bảo hành",
                        "Đổi xe mới cho khách hàng sau 1 năm sử dụng, đảm bảo chất lượng",
                        "Cung cấp miễn phí phụ tùng thay thế trong thời gian bảo trì",
                    ],
                    "question": "Chương trình chăm sóc xe miễn phí gồm những dịch vụ gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Hứa một ưu đãi đã hết hạn sẽ dẫn tới khiếu nại khi Kế toán không áp được vào đơn.",
                    "id": 3,
                    "options": [
                        "Chương trình đã hết hạn, không thể tiếp tục.",
                        "Cần phê duyệt để kéo dài chương trình.",
                        "Quy trình bảo mật nghiêm ngặt để bảo vệ thông tin.",
                        "Không có lý do cụ thể cho tình huống này.",
                    ],
                    "question": "Vì sao TVBH phải nắm thời hạn áp dụng của từng ưu đãi?",
                },
            ],
            "resources": [
                {
                    "name": "Đào tạo Chương trình chăm sóc xe miễn phí",
                    "path": "s3://General_doc/CTKM/Đào tạo Chương trình chăm sóc xe miễn phí_0043.pptx",
                    "type": "doc",
                },
                {
                    "name": "VF_HDSD Chương trình chăm sóc xe miễn phí",
                    "path": "KTV/VF_HDSD_HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0_7748.docx",
                    "type": "doc",
                },
            ],
            "short_title": "Khuyến mãi & Chăm sóc xe",
            "step_type": "document",
            "title": "Chương trình Khuyến mãi & Chăm sóc Xe miễn phí",
        },
    ],
    "technician": [
        {
            "duration_minutes": 2,
            "goal": "Nắm vững phạm vi & điều kiện bảo hành Xe máy điện VF (khung sườn, động cơ, khối Pin "
            "LFP). Biết quy trình tiếp nhận xe bảo hành chuẩn cho xưởng dịch vụ 3S mới khai "
            "trương.",
            "guides": [
                {
                    "desc": "Khung sườn / Động cơ / Pin LFP — nắm rõ điều kiện được và không được bảo hành.",
                    "letter": "A",
                    "title": "Phạm vi bảo hành",
                },
                {
                    "desc": "Kiểm tra giấy tờ → Điền phiếu kiểm tra → Chụp ảnh tình trạng xe → Giao cho KTV phân công.",
                    "letter": "B",
                    "title": "Tiếp nhận xe",
                },
                {
                    "desc": "Các bước nghiệp vụ setup xưởng, phân luồng xe bảo hành và xe sửa chữa thường.",
                    "letter": "C",
                    "title": "Xưởng 3S mở mới",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Chính sách bảo hành loại trừ hư hỏng do dùng nguồn sạc không đúng chuẩn của VF.",
                    "id": 1,
                    "options": [
                        "Không đủ điều kiện bảo hành do sử dụng sai quy cách",
                        "Có, bảo hành vô điều kiện trong thời gian quy định",
                        "Có, nếu khách hàng yêu cầu và có lý do chính đáng",
                        "Quyết định bảo hành dựa trên tình huống và quy trình",
                    ],
                    "question": "Pin LFP phồng do khách tự sạc nguồn không chuẩn có được bảo hành?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Bốn bước này đảm bảo có đủ bằng chứng hiện trạng xe trước khi vào xưởng.",
                    "id": 2,
                    "options": [
                        "Quy trình 4 bước: kiểm tra giấy tờ, điền phiếu, chụp ảnh, phân công KTV",
                        "Chỉ thực hiện 1 bước mà không cần thông tin thêm",
                        "Quy trình có thể kéo dài đến 10 bước phức tạp",
                        "Không có quy trình cố định, tùy thuộc từng trường hợp",
                    ],
                    "question": "Quy trình tiếp nhận xe bảo hành có mấy bước chính?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Ba nhóm này là phạm vi bảo hành chính, mỗi nhóm có thời hạn và điều kiện riêng.",
                    "id": 3,
                    "options": [
                        "Khung sườn, động cơ và pin LFP là thành phần chính của xe điện",
                        "Thay lốp mà không kiểm tra bộ phận khác gây mất an toàn",
                        "Chỉ chăm sóc sơn mà bỏ qua kỹ thuật không đảm bảo chất lượng",
                        "Xem xét toàn bộ bộ phận là cách tiếp cận hiệu quả nhất",
                    ],
                    "question": "Những bộ phận nào của xe XMĐ nằm trong phạm vi bảo hành?",
                },
            ],
            "resources": [
                {
                    "name": "1. Tài liệu Tự hào VinGroup",
                    "path": "s3://General_doc/TaiLieuChung/1. Tài liệu Tự hào VinGroup.pdf",
                    "type": "doc",
                },
                {
                    "name": "2. Lịch sử & Tổng quan sản phẩm XMĐ",
                    "path": "s3://General_doc/TaiLieuChung/2. Lịch sử & Tổng quan sản phẩm XMĐ_260617.pdf",
                    "type": "doc",
                },
            ],
            "short_title": "Chính sách Bảo hành",
            "step_type": "document",
            "title": "Chào mừng & Chính sách Bảo hành XMĐ VinFast",
        },
        {
            "duration_minutes": 3,
            "goal": "Thao tác DMS xưởng thành thạo: Đăng nhập → Tra cứu lịch sử xe theo số VIN → Kiểm "
            "tra bảo hành còn hiệu lực → Mở Lệnh sửa chữa RO đúng loại → Lập Phiếu tiếp nhận xe.",
            "guides": [
                {
                    "desc": "URL → Chọn đại lý → Vào giao diện Xưởng dịch vụ / Service.",
                    "letter": "A",
                    "title": "Đăng nhập DMS xưởng",
                },
                {
                    "desc": "Nhập số khung VIN → Xem lịch sử bảo dưỡng, bảo hành đã thực hiện trước đó.",
                    "letter": "B",
                    "title": "Tra cứu xe theo VIN",
                },
                {
                    "desc": "Đối chiếu ngày mua xe và số km thực tế với chính sách bảo hành.",
                    "letter": "C",
                    "title": "Kiểm tra bảo hành còn hiệu lực",
                },
                {
                    "desc": "Chọn loại lệnh (Bảo hành / Sửa chữa thường / Bảo dưỡng định kỳ) → "
                    "Nhập mô tả triệu chứng của khách.",
                    "letter": "D",
                    "title": "Mở Lệnh RO",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "VIN là định danh duy nhất của xe, gắn với toàn bộ lịch sử bảo hành, bảo dưỡng.",
                    "id": 1,
                    "options": [
                        "Số khung VIN xác định và theo dõi lịch sử xe.",
                        "Tên khách hàng giúp xác định danh tính trong giao dịch.",
                        "Biển số xe giúp nhận diện và quản lý phương tiện.",
                        "Số điện thoại khách hỗ trợ liên lạc và hỗ trợ khi cần.",
                    ],
                    "question": "Để tra cứu lịch sử bảo hành xe, cần nhập thông tin gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Chi phí RO bảo hành do VF chi trả nên bắt buộc phải có đề xuất và phê duyệt.",
                    "id": 2,
                    "options": [
                        "RO bảo hành cần phê duyệt chi phí bởi VF trước khi thực hiện",
                        "Quy trình bảo hành và sửa chữa không khác biệt rõ ràng",
                        "Khách hàng có thể mở RO bảo hành mà không cần nhân viên",
                        "RO sửa chữa không yêu cầu lập phiếu, tiết kiệm thời gian",
                    ],
                    "question": "Mở lệnh RO loại Bảo hành khác gì với Sửa chữa thường?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Phải xác định bảo hành còn hiệu lực trước, nếu không sẽ chọn sai loại lệnh RO.",
                    "id": 3,
                    "options": [
                        "Đối chiếu ngày mua và số km với chính sách bảo hành",
                        "Kiểm tra màu sơn để phát hiện hư hỏng hoặc trầy xước",
                        "Hỏi giá bán lại để đánh giá giá trị thị trường xe",
                        "Không cần kiểm tra, chỉ sử dụng xe mà không quan tâm",
                    ],
                    "question": "Trước khi mở RO cần kiểm tra điều gì về bảo hành của xe?",
                },
            ],
            "resources": [
                {
                    "name": "01. Hướng dẫn đăng nhập DMS",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/Khác/01. Hướng dẫn đăng nhập DMS.mp4",
                    "type": "video",
                },
                {"name": "2. Thông tin xe", "path": "s3://KTV/2. Đào tạo VF_HM55 cho XMĐ.pdf", "type": "video"},
                {
                    "name": "5. Tạo lệnh sửa chữa",
                    "path": "s3://KTV/Bảo hành _ Chính sách & Quy trình bảo hành/260727-VF_HMVN_Đào tạo Bảo hành XDV XMĐ mở mới.pptx",
                    "type": "video",
                },
                {
                    "name": "Phiếu sửa chữa cập nhật",
                    "path": "s3://KTV/Bảo hành _ Chính sách & Quy trình bảo hành/260727-VF_HMVN_Đào tạo Bảo hành XDV XMĐ mở mới.pptx",
                    "type": "doc",
                },
            ],
            "short_title": "Tra cứu xe & Mở lệnh RO",
            "step_type": "task",
            "title": "Đăng nhập DMS, Tra cứu Thông tin Xe & Mở Lệnh Sửa chữa (RO)",
        },
        {
            "duration_minutes": 3,
            "goal": "Nắm luồng chẩn đoán & xử lý sự cố khối Pin LFP — đặc thù riêng của xe máy điện VF. "
            "Lập đề xuất linh kiện cần thay thế và gửi Yêu cầu bảo hành về kho tổng VinFast trên "
            "DMS.",
            "guides": [
                {
                    "desc": "Dùng thiết bị chẩn đoán → Đọc mã lỗi → Phân loại sự cố (Cell hỏng "
                    "/ BMS lỗi / Connector) → Tham chiếu Hướng dẫn luồng sửa chữa Pin "
                    "XMĐ.",
                    "letter": "A",
                    "title": "Chẩn đoán Pin LFP",
                },
                {
                    "desc": "Từ RO đang mở → Thêm đề xuất linh kiện → Nhập mã linh kiện và số lượng → Gửi duyệt.",
                    "letter": "B",
                    "title": "Lập đề xuất linh kiện trên DMS",
                },
                {
                    "desc": "Sau khi VF phê duyệt, linh kiện được xuất từ kho tổng → Nhận về "
                    "xưởng và tiến hành thay thế.",
                    "letter": "C",
                    "title": "Theo dõi phê duyệt",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Khối pin là cụm kín; xưởng không được tự tháo thay từng cell "
                    "mà phải thay theo cụm.",
                    "id": 1,
                    "options": [
                        "Thay toàn bộ khối pin theo quy định để đảm bảo an toàn và hiệu suất",
                        "Thay dây điện hỏng mà không kiểm tra các bộ phận khác",
                        "Thay lốp xe mà không kiểm tra phanh và hệ thống treo",
                        "Thay động cơ mà không xem xét hệ thống truyền động và điện tử",
                    ],
                    "question": "Pin LFP bị hỏng cell thì cần thay thế bộ phận nào?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Linh kiện chỉ được xuất kho sau phê duyệt, KTV nhận về rồi mới thực hiện thay thế.",
                    "id": 2,
                    "options": [
                        "Nhận linh kiện từ kho và thay thế theo tiêu chuẩn kỹ thuật",
                        "Đóng lệnh RO mà không xem xét tình trạng xe và yêu cầu khách",
                        "Trả xe cho khách trước khi hoàn tất kiểm tra chất lượng",
                        "Hủy đề xuất mà không xác minh lý do hoặc thông báo liên quan",
                    ],
                    "question": "Sau khi đề xuất được VF phê duyệt, KTV cần làm gì tiếp?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Bảng luồng sửa chữa Pin cho XDV quy định cách phân loại lỗi "
                    "và hướng xử lý tương ứng.",
                    "id": 3,
                    "options": [
                        "Hướng dẫn sửa chữa Pin xe máy điện, kiểm tra và thay linh kiện.",
                        "Chính sách bán hàng xe máy điện, khuyến mãi, bảo hành và giá cả.",
                        "Bảng kê N677, liệt kê linh kiện và phụ tùng sửa chữa xe máy điện.",
                        "Danh sách kiểm tra showroom, tiêu chí đánh giá chất lượng trưng bày.",
                    ],
                    "question": "Tài liệu nào dùng để tham chiếu khi phân loại sự cố Pin LFP?",
                },
            ],
            "resources": [
                {
                    "name": "Hướng dẫn luồng sửa chữa Pin XMĐ cho XDV",
                    "path": "s3://KTV/Bảo hành _ Chính sách & Quy trình bảo hành/Hướng dẫn luồng sửa chữa Pin XMĐ cho XDV_new2.xlsx",
                    "type": "doc",
                },
                {
                    "name": "6. Đề xuất bảo hành",
                    "path": "s3://KTV/Bảo hành _ Chính sách & Quy trình bảo hành/Hướng dẫn luồng sửa chữa Pin XMĐ cho XDV_new2.xlsx",
                    "type": "video",
                },
            ],
            "short_title": "Chẩn đoán Pin LFP",
            "step_type": "task",
            "title": "Chẩn đoán Pin LFP & Đề xuất Linh kiện Bảo hành",
        },
        {
            "duration_minutes": 2,
            "goal": "Thiết lập cam kết thời gian giao xe (SLA) trên DMS. Kiểm tra và báo cáo tồn kho phụ "
            "tùng xưởng. Thực hiện kiểm tra QC chất lượng trước khi giao xe cho khách.",
            "guides": [
                {
                    "desc": "Từ RO → Thêm cam kết thời gian → Nhập ngày hẹn giao xe → Thông "
                    "báo cho khách qua DMS hoặc điện thoại.",
                    "letter": "A",
                    "title": "Cam kết SLA",
                },
                {
                    "desc": "Vào mục Tồn kho → Xuất báo cáo số lượng phụ tùng hiện có → Báo Kế "
                    "toán đặt bổ sung nếu thiếu.",
                    "letter": "B",
                    "title": "Kiểm tra tồn kho phụ tùng",
                },
                {
                    "desc": "Checklist kiểm tra xe sau sửa chữa → Ký phiếu bàn giao → Đóng lệnh RO trên DMS.",
                    "letter": "C",
                    "title": "QC trước giao xe",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "Cam kết SLA gắn với RO và ghi nhận ngày hẹn trả xe để khách theo dõi.",
                    "id": 1,
                    "options": [
                        "Xác định ngày giao xe để đảm bảo tiến độ và hài lòng khách hàng",
                        "Tính giá bán xe dựa trên chi phí, thị trường và khuyến mãi",
                        "Cung cấp số điện thoại quản lý để khách hàng liên hệ hỗ trợ",
                        "Chọn màu sơn xe theo sở thích khách và xu hướng thị trường",
                    ],
                    "question": "KTV cần nhập thông tin gì khi tạo cam kết thời gian SLA?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Kế toán là bộ phận lập PO đặt phụ tùng với VF, nên phải được báo sớm.",
                    "id": 2,
                    "options": [
                        "Liên hệ Kế toán để đặt hàng bổ sung theo quy trình",
                        "Không thông báo cho ai, làm theo ý mình",
                        "Thông báo khách hàng về tình trạng hàng hóa và yêu cầu",
                        "Mua hàng từ nguồn bên ngoài mà không kiểm tra chất lượng",
                    ],
                    "question": "Phụ tùng tồn kho xưởng đã hết thì KTV thông báo cho ai?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Đóng RO đánh dấu lượt dịch vụ hoàn tất và chốt số liệu cho báo cáo xưởng.",
                    "id": 3,
                    "options": [
                        "Đóng lệnh RO, hoàn tất quy trình và ghi nhận kết quả giao dịch",
                        "Mở lệnh RO mới để theo dõi và quản lý yêu cầu dịch vụ",
                        "Xóa lịch sử xe để cập nhật thông tin chính xác hơn",
                        "Hủy cam kết SLA để điều chỉnh yêu cầu dịch vụ thực tế",
                    ],
                    "question": "Thao tác cuối cùng trên DMS sau khi QC và bàn giao xe là gì?",
                },
            ],
            "resources": [
                {
                    "name": "9. Tạo cam kết thời gian sửa chữa",
                    "path": "s3://KTV/Bảo hành _ Chính sách & Quy trình bảo hành/1. Chinh sach bao hanh XMĐ TTVN.pdf",
                    "type": "video",
                },
                {
                    "name": "1. Kiểm tra và xuất số lượng tồn kho phụ tùng",
                    "path": "s3://KeToan/Hướng dẫn hệ thống DMS/3. Xem tồn/1. Kiểm tra và xuất số lượng tồn kho phụ tùng.mp4",
                    "type": "video",
                },
            ],
            "short_title": "Cam kết SLA & QC",
            "step_type": "task",
            "title": "Cam kết Thời gian SLA, Tồn kho Phụ tùng & QC Xuất xưởng",
        },
        {
            "duration_minutes": 2,
            "goal": "Nắm được các chương trình khuyến mãi & ưu đãi hiện hành, chương trình Chăm sóc xe "
            "miễn phí để có thể giải thích chính xác khi khách hỏi ngay tại xưởng dịch vụ.",
            "guides": [
                {
                    "desc": "E-Voucher, quà tặng kèm, ưu đãi CBNV — KTV KHÔNG nhập KM trên DMS "
                    "nhưng phải biết để giải thích đúng cho khách tại xưởng.",
                    "letter": "A",
                    "title": "Các ưu đãi & KM hiện hành",
                },
                {
                    "desc": "Biết nội dung chương trình (kiểm tra xe, bơm lốp, vệ sinh miễn "
                    "phí) để hướng dẫn khách đăng ký khi đưa xe vào bảo dưỡng.",
                    "letter": "B",
                    "title": "Chăm sóc xe miễn phí",
                },
            ],
            "quiz": [
                {
                    "correctIndex": 0,
                    "explanation": "KTV cần nắm điều kiện áp dụng để trả lời chính xác và hướng "
                    "dẫn khách đăng ký đúng cách.",
                    "id": 1,
                    "options": [
                        "Đối chiếu điều kiện khuyến mãi và hướng dẫn đăng ký tại xưởng",
                        "Thông báo không có chương trình khuyến mãi và lý do cụ thể",
                        "Cam kết miễn phí dịch vụ trong khuyến mãi và thông tin ưu đãi khác",
                        "Khuyến khích khách tự tìm hiểu thông tin và tài liệu tham khảo",
                    ],
                    "question": "Khách hỏi 'xe tôi có được chăm sóc miễn phí không' — trả lời sao?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Chương trình chỉ bao gồm các hạng mục chăm sóc cơ bản, không "
                    "thay thế linh kiện lớn.",
                    "id": 2,
                    "options": [
                        "Kiểm tra xe, bơm lốp, vệ sinh xe miễn phí cho khách",
                        "Thay pin miễn phí cho xe trong thời gian bảo hành",
                        "Đổi xe mới nếu xe gặp sự cố nghiêm trọng",
                        "Sửa chữa hư hỏng miễn phí, bao gồm động cơ và điện",
                    ],
                    "question": "Chương trình chăm sóc xe miễn phí gồm những dịch vụ gì?",
                },
                {
                    "correctIndex": 0,
                    "explanation": "Phân quyền rõ ràng: KTV nắm thông tin để tư vấn, thao tác nhập thuộc về Kế toán.",
                    "id": 3,
                    "options": [
                        "Kế toán mới có quyền nhập dữ liệu, KTV chỉ hướng dẫn khách hàng.",
                        "KTV có thể nhập thông tin nếu được cấp quyền và đào tạo.",
                        "KTV nhập dữ liệu nếu khách hàng yêu cầu và được quản lý đồng ý.",
                        "KTV có thể nhập thông tin trong trường hợp khẩn cấp nếu cần.",
                    ],
                    "question": "Kỹ thuật viên có được nhập khuyến mãi trên DMS không?",
                },
            ],
            "resources": [
                {
                    "name": "Đào tạo Chương trình chăm sóc xe miễn phí",
                    "path": "General_doc/Đào tạo Chương trình chăm sóc xe miễn phí_0043.pptx",
                    "type": "doc",
                },
                {
                    "name": "VF_HDSD Chương trình chăm sóc xe miễn phí",
                    "path": "KTV/VF_HDSD_HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0_7748.docx",
                    "type": "doc",
                },
            ],
            "short_title": "Khuyến mãi & Chăm sóc xe",
            "step_type": "document",
            "title": "Chương trình Khuyến mãi & Chăm sóc Xe miễn phí",
        },
    ],
}

PLAN_ROLES = tuple(ROLE_ONBOARDING_CATALOG.keys())


def all_resource_paths() -> set[str]:
    """Tập hợp mọi đường dẫn tài liệu được tham chiếu trong catalog."""
    role_paths = {
        unicodedata.normalize("NFC", res["path"])
        for steps in ROLE_ONBOARDING_CATALOG.values()
        for step in steps
        for res in step["resources"]
    }
    common_paths = {unicodedata.normalize("NFC", res["path"]) for res in COMMON_OVERVIEW_RESOURCES}
    return role_paths | common_paths


@cache
def resource_paths_for_role(role: str) -> frozenset[str]:
    """Đường dẫn tài liệu mà một vai trò được phép truy cập (dùng cho RBAC)."""
    role_paths = {
        unicodedata.normalize("NFC", res["path"])
        for step in ROLE_ONBOARDING_CATALOG.get(role, [])
        for res in step["resources"]
    }
    common_paths = {unicodedata.normalize("NFC", res["path"]) for res in COMMON_OVERVIEW_RESOURCES}
    return frozenset(role_paths | common_paths)


def resource_modules_for_role(role: str, path: str) -> set[int]:
    """Return module IDs containing a resource for the selected role."""
    normalized = unicodedata.normalize("NFC", path)
    steps = ROLE_ONBOARDING_CATALOG.get(role, [])
    total = len(steps)
    modules: set[int] = set()
    for index, step in enumerate(steps, start=1):
        module_id = 1 if index == 1 else 3 if index == total else 2
        if any(unicodedata.normalize("NFC", item["path"]) == normalized for item in step["resources"]):
            modules.add(module_id)
    if any(unicodedata.normalize("NFC", item["path"]) == normalized for item in COMMON_OVERVIEW_RESOURCES):
        modules.add(1)
    return modules
