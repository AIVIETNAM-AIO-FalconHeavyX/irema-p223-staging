# 📊 Evaluation Evidence Report (Báo Cáo Đánh Giá Chất Lượng System)
## VF AI Onboarding Agent — Team The Sigmoid (P-223)

> **Dự án:** VF AI Onboarding Agent (Hệ thống onboarding & trợ lý AI đại lý xe máy điện VinFast)  
> **Thời gian đánh giá:** 2026-08-16  
> **Môi trường:** Production/Local Benchmark (LangGraph + Hybrid Search + CrossEncoder Reranker + ChromaDB + BM25)  

---

## 1. Manual Test Cases (6 Test Cases Thực Tế kèm Output)

Dưới đây là **6 manual test cases thực tế** chạy qua toàn bộ pipeline AI Assistant (Role Verification → Smart Controller Router → Hybrid Retrieval → CrossEncoder Reranking → Response Generation).

---

### 📝 Test Case 1: Q001 — Tiêu Chuẩn Diện Mạo & Tác Phong Nhân Sự Bán Hàng

- **Test Case ID:** `Q001`
- **User Role:** `sales` (Nhân viên tư vấn bán hàng đại lý)
- **Loại Query:** Procedural & Service Standards Text Query
- **Câu hỏi (Query):** *"Tiêu chuẩn về diện mạo tác phong và giao tiếp nhân sự bán hàng xe máy điện"*
- **Expected Doc ID:** `SALE003` (`3_1_tieu_chuan_dich_vu_xmd_251121.pdf`)
- **Latency Xử lý:** `1.857s`
- **Role Isolation Check:** ✅ **PASS** (`sales` truy cập tài liệu `sales` & `general`, không lộ tài liệu kỹ thuật/kế toán)

#### 🔍 Retrieved Sources (Top Trích dẫn):
1. **Document:** `3.1 Tiêu chuẩn dịch vụ XMĐ 251121` | **Section:** `Slide 2` | **Role:** `sales` | **Score:** `5.458`
2. **Document:** `3.1 Tiêu chuẩn dịch vụ XMĐ 251121` | **Section:** `Slide 38` | **Role:** `sales` | **Score:** `5.404`
3. **Document:** `3.1 Tiêu chuẩn dịch vụ XMĐ 251121` | **Section:** `Slide 60` | **Role:** `sales` | **Score:** `5.002`

#### 🤖 Output Thực Tế Từ AI Assistant:
> Dưới đây là các **Tiêu chuẩn cốt lõi về diện mạo, tác phong và giao tiếp** dành cho nhân sự bán hàng xe máy điện VinFast:
> 
> 1. **Diện mạo & Trang phục:**
>    - Đồng phục đúng quy định Showroom, sạch sẽ, phẳng phiu; đeo thẻ tên đúng vị trí.
>    - Tác phong nhanh nhẹn, chuyên nghiệp, giữ nét mặt tươi tắn và thái độ niềm nở.
> 
> 2. **Giao tiếp & Thái độ với Khách hàng:**
>    - Quy tắc *"Nhường đường"*: Luôn nhường khách đi trước hoặc sử dụng dịch vụ trước.
>    - Quy tắc *"2 tay"*: Mọi tài liệu, chìa khóa xe, quà tặng đều được đưa/nhận bằng hai tay.
>    - Lắng nghe chân thành, chủ động nắm tên khách hàng và xưng hô lịch sự trong suốt quá trình tư vấn.
> 
> 3. **Chuẩn bị Tài liệu & Tư vấn:**
>    - Chuẩn bị đầy đủ bảng giá, brochure, chương trình ưu đãi mới nhất trước khi tiếp đón khách.
> 
> 📌 *Nguồn trích dẫn:* `3.1 Tiêu chuẩn dịch vụ XMĐ 251121 (Slide 2)`, `3.1 Tiêu chuẩn dịch vụ XMĐ 251121 (Slide 38)`

---

### 📝 Test Case 2: Q002 — Thời Gian Bảo Hành Pin LFP & Ắc Quy 12V Xe Máy Điện

- **Test Case ID:** `Q002`
- **User Role:** `technician` (Kỹ thuật viên 3S xưởng dịch vụ)
- **Loại Query:** Tabular Data Query (Truy xuất dữ liệu bảng biểu chính xác)
- **Câu hỏi (Query):** *"Thời gian bảo hành pin LFP và ắc quy 12V xe máy điện VinFast là bao nhiêu năm?"*
- **Expected Doc ID:** `KTV001` / `KTV260727` (`1_chinh_sach_bao_hanh_xmd_ttvn.pdf`)
- **Latency Xử lý:** `2.243s`
- **Role Isolation Check:** ✅ **PASS** (`technician` truy cập tài liệu bảo hành kỹ thuật)

#### 🔍 Retrieved Sources (Top Trích dẫn):
1. **Document:** `260727 VF HMVN Đào tạo Bảo hành XDV XMĐ mở mới` | **Section:** `V. Lưu trình lưu trữ & Hủy phụ tùng` | **Role:** `technician` | **Score:** `5.295`
2. **Document:** `1. Chính sách bảo hành XMĐ TTVN` | **Section:** `2. Chính sách phụ tùng thay thế` | **Role:** `technician` | **Score:** `3.804`

#### 🤖 Output Thực Tế Từ AI Assistant:
> Căn cứ theo **Chính sách bảo hành xe máy điện VinFast TTVN**, thời gian bảo hành cụ thể cho từng hạng mục như sau:
> 
> | Hạng mục phụ tùng / Linh kiện | Thời gian bảo hành tiêu chuẩn | Điều kiện Km đi kèm |
> |--------------------------------|-------------------------------|---------------------|
> | **Pin LFP (Bộ pin động lực)** | **6 năm** | Không giới hạn số Km |
> | **Ắc quy 12V tiêu chuẩn** | **1 năm** | Hoặc theo số km quy định |
> | **Phụ tùng thay thế bảo hành** | Theo thời hạn còn lại của xe hoặc **1 năm** | Tùy điều kiện nào đến trước |
> 
> 💡 *Lưu ý kỹ thuật:* Đối với trường hợp thay thế phụ tùng bảo hành, thời gian bảo hành mới tính từ ngày xuất hóa đơn phụ tùng ghi nhận trên hệ thống DMS.
> 
> 📌 *Nguồn trích dẫn:* `1. Chính sách bảo hành XMĐ TTVN (2. Chính sách phụ tùng thay thế)`, `260727 VF HMVN Đào tạo Bảo hành XDV XMĐ mở mới`

---

### 📝 Test Case 3: Q003 — Hướng Dẫn Đăng Nhập DMS & Kiểm Tra Trùng Lead

- **Test Case ID:** `Q003`
- **User Role:** `accounting` (Kế toán viên Đại lý Phân phối)
- **Loại Query:** Procedure & Video Transcription Search (Xử lý dữ liệu từ Video MP4)
- **Câu hỏi (Query):** *"Hướng dẫn đăng nhập hệ thống DMS và quy luật kiểm tra trùng khi tạo lead"*
- **Expected Doc ID:** `KETO003` (`03_quy_luat_kiem_tra_trung_khi_tao_lead.mp4` transcript)
- **Latency Xử lý:** `2.388s`
- **Role Isolation Check:** ✅ **PASS** (`accounting` truy cập video hướng dẫn nghiệp vụ Kế toán/DMS)

#### 🔍 Retrieved Sources (Top Trích dẫn):
1. **Document:** `03. Quy luật kiểm tra trùng khi tạo Lead` | **Section:** `00:00 - 02:31` | **Role:** `accounting` | **Score:** `6.531`
2. **Document:** `03. Quy luật kiểm tra trùng khi tạo Lead` | **Section:** `02:37 - 04:53` | **Role:** `accounting` | **Score:** `6.389`
3. **Document:** `03. Quy luật kiểm tra trùng khi tạo Lead` | **Section:** `01:57` | **Role:** `accounting` | **Score:** `6.006`

#### 🤖 Output Thực Tế Từ AI Assistant:
> Dưới đây là **Quy luật kiểm tra trùng (Duplicate Check Rule)** khi khởi tạo Khách hàng tiềm năng (Lead) trên hệ thống DMS:
> 
> 1. **Điều kiện kiểm tra trùng số điện thoại:**
>    - Khi tạo Lead mới có **Số điện thoại** trùng với số điện thoại đã tồn tại ở đơn vị (BU) khác trong thời gian **dưới 30 ngày**, hệ thống sẽ đưa ra cảnh báo.
>    - Cảnh báo mẫu: *"Số điện thoại này đã được tạo ở BU [Name] chưa quá 30 ngày"*.
> 
> 2. **Xử lý cho phép tạo Lead:**
>    - Nếu trường hợp tạo ở cơ sở đại lý của mình, hệ thống vẫn cho phép bấm **OK** để tiếp tục duy trì và điều hướng thông tin Lead.
> 
> 📌 *Nguồn trích dẫn:* `03. Quy luật kiểm tra trùng khi tạo Lead (00:00 - 02:31)`, `03. Quy luật kiểm tra trùng khi tạo Lead (01:57)`

---

### 📝 Test Case 4: Q004 — Quy Trình Claim Bù Tồn Kho Xe Máy Điện Dành Cho ĐLPP

- **Test Case ID:** `Q004`
- **User Role:** `technician` (Kỹ thuật viên / Quản lý kho dịch vụ)
- **Loại Query:** Operational Process & Claim Workflow
- **Câu hỏi (Query):** *"Quy trình claim bù tồn kho xe máy điện dành cho nhà phân phối"*
- **Expected Doc ID:** `KTV001` / `KTV002` (`vf_hdsd_luong_claim_bu_ton.docx`)
- **Latency Xử lý:** `2.358s`
- **Role Isolation Check:** ✅ **PASS** (`technician` truy cập tài liệu vận hành dịch vụ & claim)

#### 🔍 Retrieved Sources (Top Trích dẫn):
1. **Document:** `VF HDSD Chương trình Chăm sóc xe Miễn phí dành cho VinFast` | **Section:** `VII. 7.1. Sử dụng voucher` | **Role:** `technician` | **Score:** `3.818`
2. **Document:** `2. Đào tạo VF HM55 cho XMĐ` | **Section:** `2. QUY TRÌNH VẬN HÀNH XDV TOÀN CẦU` | **Role:** `technician` | **Score:** `2.943`

#### 🤖 Output Thực Tế Từ AI Assistant:
> **Quy trình Claim bù tồn kho xe máy điện** được thực hiện theo các bước chuẩn chuẩn hóa sau:
> 
> 1. **Khởi tạo yêu cầu Claim:**
>    - Kỹ thuật viên/Kế toán dịch vụ kiểm tra phụ tùng/xe cần claim bù tồn kho trên hệ thống DMS.
>    - Lập Phiếu đề nghị Claim đính kèm Biên bản kiểm tra kỹ thuật & mã định danh VIN/Serial.
> 
> 2. **Phê duyệt & Lưu trữ:**
>    - Đại lý lưu trữ đầy đủ hồ sơ claim và tiến hành luân chuyển thông tin theo **Quy trình vận hành XDV toàn cầu**.
>    - Đợi xác nhận phê duyệt từ Trụ sở VinFast (HMVN) trước khi xuất/nhập bù kho.
> 
> 💡 Gợi ý: Bạn có muốn hỏi chi tiết hơn về từng bước trong quy trình trên không?
> 
> 📌 *Nguồn trích dẫn:* `2. Đào tạo VF HM55 cho XMĐ (2. QUY TRÌNH VẬN HÀNH XDV TOÀN CẦU)`

---

### 📝 Test Case 5: Q005 — Thanh Lý Chấm Dứt Hợp Đồng Thuê Pin Xe Máy Điện & Kích Hoạt Lại

- **Test Case ID:** `Q005`
- **User Role:** `accounting` (Kế toán đại lý)
- **Loại Query:** Contract & Financial Accounting Workflow
- **Câu hỏi (Query):** *"Thanh lý chấm dứt hợp đồng thuê pin xe máy điện và kích hoạt lại"*
- **Expected Doc ID:** `KETO558` (`VF_HDSD_Thanh_ly_cham_dut_doi_chu_kich_hoat_lai_HDTP.docx`)
- **Latency Xử lý:** `2.419s`
- **Role Isolation Check:** ✅ **PASS** (`accounting` truy cập tài liệu hợp đồng thuê pin Kế toán)

#### 🔍 Retrieved Sources (Top Trích dẫn):
1. **Document:** `VF HDSD Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin` | **Section:** `QUY TRÌNH CHUYỂN CHỦ HĐTP XE MAX` | **Role:** `accounting` | **Score:** `6.976`
2. **Document:** `VF HDSD Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin` | **Section:** `Mục lục` | **Role:** `accounting` | **Score:** `6.811`
3. **Document:** `VF HDSD Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin` | **Section:** `KÍCH HOẠT LẠI HĐTP CHO VINXE ĐÃ THỰC HIỆN THANH LÝ PIN VỀ VINFAST` | **Role:** `accounting` | **Score:** `6.716`

#### 🤖 Output Thực Tế Từ AI Assistant:
> Hướng dẫn chi tiết **Quy trình Thanh lý chấm dứt và Kích hoạt lại Hợp đồng Thuê pin (HĐTP)**:
> 
> 1. **Quy trình Thanh lý & Chấm dứt HĐTP:**
>    - Thu hồi pin hiện tại từ khách hàng và kiểm tra tình trạng kỹ thuật pin.
>    - Chốt chỉ số tiêu thụ/cước thuê pin còn tồn đọng và lập **Biên bản quyết toán thanh lý HĐTP**.
>    - Cập nhật trạng thái hợp đồng thành *"Đã thanh lý"* trên phân hệ Kế toán DMS.
> 
> 2. **Kích hoạt lại HĐTP (Đối với xe đã thanh lý pin về VinFast):**
>    - Thực hiện kiểm tra điều kiện xe và thông tin chủ sở hữu mới/cũ trên DMS.
>    - Gán mã Serial pin mới, lập Hợp đồng thuê pin mới và bấm **"Kích hoạt lại HĐTP"**.
> 
> 📌 *Nguồn trích dẫn:* `VF HDSD Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin (KÍCH HOẠT LẠI HĐTP CHO VINXE ĐÃ THỰC HIỆN THANH LÝ PIN VỀ VINFAST)`

---

### 🛡️ Test Case 6: Q006 — Kiểm Tra Bảo Mật Phân Quyền RBAC (Role-Based Access Control)

- **Test Case ID:** `Q006`
- **User Role:** `sales` (Nhân viên tư vấn bán hàng thử truy cập tài liệu kỹ thuật bảo mật)
- **Loại Query:** Security & Role Isolation Compliance Test
- **Câu hỏi (Query):** *"Thời gian bảo hành xe máy điện pin LFP là bao nhiêu năm"*
- **Unauthorized Roles:** `["technician"]` (Tài liệu kỹ thuật `KTV001` bị chặn tuyệt đối với role `sales`)
- **Latency Xử lý:** `2.288s`
- **Role Isolation Verification:** ✅ **PASS 100%** (Chương trình lọc sạch 100% chunk `technician` khỏi candidate pool của `sales`).

#### 🤖 Output Thực Tế Từ AI Assistant:
> Không tìm thấy thông tin phù hợp trong tài liệu được cấp quyền.
