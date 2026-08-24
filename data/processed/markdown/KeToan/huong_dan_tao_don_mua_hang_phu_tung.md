---
document_id: KETO040
title: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG
source_file: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG.docx
source_path: KeToan/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG.docx
document_type: docx
role: accounting
category: KeToan
access_scope:
- accounting
language: vi
version: '1.0'
pages: 1
pii_processed: true
pii_removed: true
processed_at: '2026-08-10'
---

# HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG

**HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG**

Tạo Đơn mua hàng là công .

Số lượng phụ tùng trên Đơn mua hàng dựa vào nhu cầu tồn kho hoặc nhu cầu từ Lệnh sửa chữa hay từ khách hàng.

1. **Kiểm tra thông tin mã phụ tùng**

1. kho &gt; Thiết lập thông tin Sản phẩm &gt; Product List.
2. Điền mã phụ tùng lọc theo từ khóa
3. Kiểm tra thông tin ngành hàng

Cơ sở double click vào bản ghi và kiểm tra ngành hàng:

2. **Kiểm tra bảng giá phụ tùng**

1. ; Thiết lập &gt; Product List &gt; .
2. Điền mã phụ tùng lọc theo từ khóa.
3. bắt đầu hiệu lực mua:

3. ****

1. ; Giao dịch &gt; Đơn mua hàng &gt; + Mới.
2. sau:

- Phân loại PR/PO: **ZVOR**
- Ngành hàng: **Phụ tùng Ô tô VF/Phụ tùng xe máy điện**
- Ưu tiên giao hàng VF: **Theo nhu cầu cơ sở**

Lưu ý với mức độ ưu tiên VOR/Khẩn cấp, cơ sở cần điền mã lệnh sửa chữa . Hệ thống lấy dòng phụ tùng trong chi tiết lệnh sửa chữa .

Cơ sở có quyền chỉnh sửa số lượng phụ tùng và xóa dòng phụ tùng, tuy nhiên không thể tự thêm dòng:

- **VF Kho/VF Sloc: Hệ thống sẽ tự điền với logic như sau:**

Các SR/ĐL khu vực miền **4013/1001**

Các SR/ĐL khu vực miền : mở kho **4013/1103**

**Các SR/ĐL khu vực miền : mở kho 4013/1010**

- **Trường hợp, hệ thống không tự điền VF Kho/VF Sloc, cơ sở vui lòng tự điền .**

3. Trên thanh công cụ, nhấn nút **Lưu / Save** ghi.
4. **Đơn hàng mua,** mở tab **Chi tiết** để nhập vào các mã Phụ tùng cần đặt mua ().

Hoặc nhấn nút **MỚI** phía nút ** / Add PO lines** trên menu .

5. Màn hình tạo **Chi tiết** thị:

Điền vào các thông tin sau:

- **Mã sản phẩm**
- **Số lượng đặt**

6. Trên thanh công cụ, nhấn nút **Lưu** ghi.
7. **Phụ tùng** sẽ hiển **** .
8. Trên thanh , nhấn **Điều khiển** và chọn status **Gửi.**
9. Trạng thái sẽ chuyển thành Đã xuống hệ thống SAP.
10. thống SAP trả về Số đơn hàng SAP, thống DMS sẽ tự động chuyển sang trạng thái hành.

4. **Phiếu nhập kho**

Cơ sở gửi số phận phân phối. phận phân phối hoàn thành dưới SAP, phiếu đẩy lên DMS.

1. ; Giao dịch &gt; Phiếu nhập kho.
2. Màn hình **Phiếu nhập kho** hiện ra với **Phiếu nhập Kho** hiện có.
3. Tìm tới **Phiếu nhập Kho** của lọc theo mã lọc theo số phiếu giao (DO) phận phân phối gửi.
4. Double click để mở **.** Kiểm tra các thông tin, ví dụ:
 - **Mã phụ tùng / Product**
 - **Số / Received Quantity**

5. Nhấn nút **Điều khiển** chọn *Phát hành* để xác nhận **Phiếu nhập kho.**