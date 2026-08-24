import json

new_lessons = [
    {
        "title": "Quản lý Đặt hàng PO (Xe & Pin)",
        "short_title": "PO Xe & Pin",
        "description": "Tạo PO mua Xe và PO Pin kèm xe, nắm rõ quy trình lên đơn và gửi duyệt VinFast.",
        "step_type": "task",
        "duration_minutes": 2,
        "goal": "Tạo thành công PO Xe (ZVOR) và PO Pin kèm xe. Nắm được các bước từ Thêm mới đến Gửi duyệt.",
        "guides": [
            {"letter": "A", "title": "Tạo PO Xe (mã ZVOR)", "desc": "Mua hàng → Thêm mới → Nhập thông tin xe, số lượng, mã đại lý → Gửi duyệt VinFast."},
            {"letter": "B", "title": "Tạo PO Pin kèm xe", "desc": "Thao tác tương tự PO Xe, lưu ý chọn đúng mã hàng là Pin tương ứng."},
        ],
        "resources_code": '''[
            _video("1. Đơn đặt hàng PO XMĐ", f"{KETOAN_NHAP_HANG}/1. Đơn đặt hàng PO XMĐ.mp4"),
            _video("3. Đơn đặt hàng PO PIN kèm xe", f"{KETOAN_NHAP_HANG}/3. Đơn đặt hàng PO PIN kèm xe.mp4"),
            _doc("Hướng dẫn tạo Đơn mua hàng xe", f"{KETOAN_NHAP_HANG_DOC}/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE.docx"),
            _doc("Hướng dẫn tạo PO đặt Pin kèm xe", f"{KETOAN_NHAP_HANG_DOC}/HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE.docx"),
        ]''',
        "quiz": [
            {
                "id": 1,
                "question": "Mã loại đơn hàng khi tạo PO mua xe XMĐ là gì?",
                "options": ["ZVOR là thuật ngữ quan trọng trong quản lý quy trình và tiêu chuẩn.", "ZSO1 là mã sản phẩm không có ý nghĩa trong quản lý.", "ZRET là thuật ngữ không chính thức, không liên quan quy trình.", "ZWAR là mã không rõ, chỉ tài liệu không chính thức trong quản lý."],
                "correctIndex": 0,
                "explanation": "Đơn mua xe/phụ tùng/pin mới từ nhà máy VF sử dụng loại chứng từ ZVOR.",
            }
        ]
    },
    {
        "title": "Quản lý Đặt hàng Phụ tùng & Nhập kho (PR)",
        "short_title": "PR & Phụ tùng",
        "description": "Tạo PO Phụ tùng, phát hành Phiếu nhập kho PR khi hàng về và kiểm tra vị trí tồn kho.",
        "step_type": "task",
        "duration_minutes": 2,
        "goal": "Biết cách đặt hàng phụ tùng hợp lệ, xử lý Phiếu nhập kho PR và kiểm kê chuyển đổi vị trí.",
        "guides": [
            {"letter": "A", "title": "Tạo PO Phụ tùng", "desc": "Mua hàng → Đặt hàng phụ tùng trong Danh sách cho phép."},
            {"letter": "B", "title": "Phát hành PR khi hàng về", "desc": "Phiếu nhập kho → Dán mã PO → Xác nhận số lượng thực nhận → Chuyển sang 'Phát hành' → Lưu."},
            {"letter": "C", "title": "Kiểm tra tồn & chuyển vị trí", "desc": "Xem tồn kho phụ tùng → Chuyển kho nếu hàng để sai vị trí."},
        ],
        "resources_code": '''[
            _video("2. Đơn đặt hàng PO phụ tùng", f"{KETOAN_NHAP_HANG}/2. Đơn đặt hàng PO phụ tùng.mp4"),
            _video("4. Phiếu nhập kho PR", f"{KETOAN_NHAP_HANG}/4. Phiếu nhập kho PR.mp4"),
            _video("1. Kiểm tra và xuất số lượng tồn kho phụ tùng", f"{KETOAN_XEM_TON}/1. Kiểm tra và xuất số lượng tồn kho phụ tùng.mp4"),
            _doc("Hướng dẫn tạo Đơn mua hàng phụ tùng", f"{KETOAN_NHAP_HANG_DOC}/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG.docx"),
            _doc("Nhập kho phụ tùng luồng mới", f"{KETOAN_NHAP_HANG_DOC}/Nhập kho phụ tùng luồng mới.docx"),
            _doc("Hướng dẫn chuyển vị trí phụ tùng trong kho DMS", f"{KETOAN_NHAP_HANG_DOC}/Hướng dẫn chuyển vị trí cho các phụ tùng trong kho DMS.docx"),
            _doc("Luồng đặt hàng phụ tùng trong Danh sách cho phép", f"{KETOAN_NHAP_HANG_DOC}/Luồng đặt hàng phụ tùng trong Danh sách cho phép.docx"),
        ]''',
        "quiz": [
            {
                "id": 2,
                "question": "Sau khi hàng về, bước tiếp theo để nhập kho là gì?",
                "options": ["Lập Phiếu nhập kho PR và chuyển sang trạng thái Phát hành.", "Xuất hóa đơn ngay sau giao dịch để đảm bảo tính hợp lệ.", "Tạo PO mới với thông tin đầy đủ để quản lý đơn hàng.", "Gửi hồ sơ Claim cho VF kèm tài liệu cần thiết để xử lý."],
                "correctIndex": 0,
                "explanation": "Chỉ khi phiếu PR được phát hành thì hàng mới ghi tăng vào tồn kho DMS.",
            }
        ]
    },
    {
        "title": "Tạo Khách hàng & Cơ hội Bán hàng",
        "short_title": "Tạo KH & Cơ hội",
        "description": "Tạo mới Khách hàng tiềm năng (Lead) và chuyển đổi thành Cơ hội trên hệ thống DMS.",
        "step_type": "task",
        "duration_minutes": 2,
        "goal": "Biết cách tạo thông tin Khách hàng, tránh trùng lặp dữ liệu và tạo thành công Cơ hội bán hàng.",
        "guides": [
            {"letter": "A", "title": "Tạo Khách hàng tiềm năng (Lead)", "desc": "Sử dụng tính năng tạo Lead và áp dụng các quy luật kiểm tra trùng lặp."},
            {"letter": "B", "title": "Tạo Cơ hội bán hàng", "desc": "Từ Khách hàng tiềm năng, chuyển đổi hoặc tạo trực tiếp Cơ hội bán hàng mới."},
        ],
        "resources_code": '''[
            _video("1. Tạo thông tin khách hàng", f"{KETOAN_DMS_CHUNG}/1. Tạo thông tin khách hàng.mp4"),
            _video("02. Tạo khách hàng tiềm năng", f"{KETOAN_KHAC}/02. Tạo khách hàng tiềm năng.mp4"),
            _video("03. Quy luật kiểm tra trùng khi tạo Lead", f"{KETOAN_KHAC}/03. Quy luật kiểm tra trùng khi tạo Lead.mp4"),
            _video("04. Cơ hội bán hàng", f"{KETOAN_KHAC}/04. Cơ hội bán hàng.mp4"),
        ]''',
        "quiz": [
            {
                "id": 1,
                "question": "Trước khi tạo Lead mới, nhân viên cần làm gì đầu tiên?",
                "options": ["Kiểm tra trùng lặp dữ liệu Khách hàng trên DMS", "Xin phê duyệt từ Quản lý đại lý", "Liên hệ khách hàng để yêu cầu cọc", "Phát hành Đơn hàng tổng"],
                "correctIndex": 0,
                "explanation": "Cần kiểm tra trùng lặp để đảm bảo dữ liệu khách hàng không bị rác trên hệ thống.",
            }
        ]
    },
    {
        "title": "Tạo Đơn hàng Tổng & Convert Đơn hàng",
        "short_title": "Tạo & Convert Đơn",
        "description": "Từ Cơ hội bán hàng, tạo Đơn hàng tổng, chọn Gói Pin (Battery Option) và Convert đơn.",
        "step_type": "task",
        "duration_minutes": 2,
        "goal": "Tạo thành công Đơn hàng tổng, xác định đúng tùy chọn Pin và hoàn tất Convert đơn.",
        "guides": [
            {"letter": "A", "title": "Tạo Đơn hàng tổng", "desc": "Từ Cơ hội, tiến hành tạo Đơn hàng tổng (ZSO1)."},
            {"letter": "B", "title": "Chọn Battery Option", "desc": "Lựa chọn chính xác hình thức Thuê pin hoặc Mua đứt pin cho khách hàng."},
            {"letter": "C", "title": "Convert Đơn hàng", "desc": "Xác nhận và Convert đơn hàng tổng sang Đơn hàng XMĐ."},
        ],
        "resources_code": '''[
            _video("05. Tạo đơn hàng tổng", f"{KETOAN_KHAC}/05. Tạo đơn hàng tổng.mp4"),
            _video("07. Battery Option", f"{KETOAN_KHAC}/07. Battery Option.mp4"),
            _video("06. Convert đơn hàng tổng với XMĐ", f"{KETOAN_KHAC}/06. Convert đơn hàng tổng với XMD.mp4"),
            _doc("Demo - Cải tiến Luồng bán XMĐ & Giao diện App XMĐ mới", f"{KETOAN_BAN_HANG}/Demo - Cải tiến Luồng bán XMĐ & Giao diện App XMĐ mới.pptx"),
            _doc("Tài liệu hướng dẫn luồng cải tiến xe máy điện", f"{KETOAN_BAN_HANG}/Tài liệu hướng dẫn sử dụng luồng cải tiến xe máy điện.docx"),
        ]''',
        "quiz": [
            {
                "id": 1,
                "question": "Chọn gói Battery Option ở bước nào trong đơn hàng DMS?",
                "options": ["Đảm bảo dữ liệu chính xác trước khi Convert Đơn hàng tổng", "Nhận phản hồi từ khách hàng sau khi giao xe hoàn tất", "Thu thập đầy đủ thông tin khi lập hồ sơ Claim", "Kiểm tra số lượng và chất lượng hàng trước khi nhập kho"],
                "correctIndex": 0,
                "explanation": "Battery Option (Thuê pin / Mua đứt pin) phải chọn ngay ở bước tạo Đơn hàng tổng.",
            }
        ]
    },
    {
        "title": "Ghép VIN & Phát hành Đơn hàng",
        "short_title": "Ghép VIN & Phát hành",
        "description": "Sau khi Convert, tiến hành Ghép số khung (VIN) vào đơn hàng và Phát hành.",
        "step_type": "task",
        "duration_minutes": 2,
        "goal": "Hoàn tất việc định danh chiếc xe cụ thể cho Khách hàng (Ghép VIN) và Phát hành đơn hàng thành công.",
        "guides": [
            {"letter": "A", "title": "Ghép số khung (VIN)", "desc": "Vào kho xe, chọn đúng VIN và ghép vào Đơn hàng đã Convert."},
            {"letter": "B", "title": "Phát hành Đơn hàng", "desc": "Kiểm tra lại toàn bộ thông tin và nhấn Phát hành đơn hàng để chốt thông tin."},
        ],
        "resources_code": '''[
            _video("12. Ghép xe", f"{KETOAN_KHAC}/12. Ghép xe.mp4"),
            _video("11. Phát hành đơn hàng", f"{KETOAN_KHAC}/11. Phát hành đơn hàng.mp4"),
            _video("Video hướng dẫn DMS luồng mới", f"{KETOAN_BAN_HANG}/Video hướng dẫn DMS luồng mới.mp4"),
        ]''',
        "quiz": [
            {
                "id": 1,
                "question": "Ghép xe VIN vào đơn thực hiện ở giai đoạn nào của luồng bán?",
                "options": ["Hoàn tất Convert và phát hành đơn hàng cho khách hàng", "Liên hệ và tư vấn khách hàng ngay khi tạo Lead", "Kiểm tra và xác nhận thông tin thanh toán sau xuất hóa đơn", "Phân tích thị trường và xác định nhu cầu trước khi tạo Cơ hội"],
                "correctIndex": 0,
                "explanation": "Đơn phải được convert và phát hành thì mới ghép được số khung VIN từ kho xe.",
            }
        ]
    },
    {
        "title": "Quản lý Hợp đồng Thuê Pin",
        "short_title": "Hợp đồng Pin",
        "description": "Ký Hợp đồng thuê Pin, biên bản bàn giao và xử lý các nghiệp vụ đổi chủ, chấm dứt.",
        "step_type": "task",
        "duration_minutes": 3,
        "goal": "Hiểu rõ quy trình tạo Hợp đồng thuê Pin (HĐTP), in và cho khách ký các biên bản liên quan đến Pin.",
        "guides": [
            {"letter": "A", "title": "Tạo Hợp đồng thuê Pin", "desc": "Trên DMS, tạo HĐTP và in để khách hàng ký."},
            {"letter": "B", "title": "Thanh lý / Đổi chủ HĐTP", "desc": "Các thủ tục khi khách hàng có nhu cầu chấm dứt hoặc bán lại xe đổi chủ."},
            {"letter": "C", "title": "Biên bản bàn giao Pin", "desc": "Hoàn tất biên bản bàn giao hoặc hoàn chuyển cọc Pin."},
        ],
        "resources_code": '''[
            _video("13. Hợp đồng thuê PIN", f"{KETOAN_KHAC}/13. Hợp đồng thuê PIN.mp4"),
            _doc("VF_HDSD Bán hàng XMĐ thuê Pin trả trước Model MAX", f"{KETOAN_HDTP}/VF _HDSD_Bán hàng XMĐ thuê Pin trả trước Model MAX v0.4_4508.pdf"),
            _doc("VF_PC01.118 Hợp đồng cho thuê pin", f"{KETOAN_DAO_TAO}/Tài liệu tham khảo khác/VF_PC01.118_HD cho thue pin_05.03.2026.docx"),
            _doc("VF_HDSD Thanh lý, chấm dứt, đổi chủ, kích hoạt lại HĐTP", f"{KETOAN_HDTP}/VF_HDSD_Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin.docx"),
            _doc("BB chấm dứt sử dụng dịch vụ thuê pin XMĐ", f"{KETOAN_HDTP_KY}/BB chấm dứt sử dụng dịch vụ thuê pin - XMĐ.docx"),
            _doc("Biên bản bàn giao pin (chấm dứt dịch vụ & đổi chủ)", f"{KETOAN_HDTP_KY}/Biên bản bàn giao pin nghiệp vụ chấm dứt dịch vụ và đổi chủ XMĐ.docx"),
            _doc("Giấy yêu cầu hoàn, chuyển cọc LFP", f"{KETOAN_HDTP_KY}/Giấy yêu cầu hoàn, chuyển cọc LFP 20230406.docx"),
        ]''',
        "quiz": [
            {
                "id": 1,
                "question": "Muốn hủy HĐTP khi khách đổi xe, Kế toán cần làm thủ tục gì?",
                "options": ["Thực hiện thủ tục thanh lý hợp đồng theo giấy tờ khách hàng đã ký", "Xóa hợp đồng mà không kiểm tra thông tin hợp lệ", "Không thực hiện hành động nào với hợp đồng hiện tại", "Sửa đổi nội dung hợp đồng cũ mà không có sự đồng ý"],
                "correctIndex": 0,
                "explanation": "Có bộ tài liệu riêng cho Thanh lý/Chấm dứt/Đổi chủ HĐTP kèm biên bản khách phải ký.",
            }
        ]
    }
]

import textwrap

out_str = ""
for item in new_lessons:
    res_code = item.pop("resources_code")
    item_str = json.dumps(item, ensure_ascii=False, indent=4)
    # Replace resources string placeholder with actual code
    item_str = item_str[:-2] + f',\n        "resources": {res_code.strip()}' + "\n    },"
    # Need to properly indent
    
    lines = item_str.split('\\n')
    indented = "\\n".join(["        " + line if i > 0 else line for i, line in enumerate(lines)])
    out_str += "        " + item_str + "\n"

with open("output_lessons.txt", "w", encoding="utf-8") as f:
    f.write(out_str)
