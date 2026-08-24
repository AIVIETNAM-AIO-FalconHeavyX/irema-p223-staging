---
document_id: KETO428
title: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE
source_file: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE.docx
source_path: KeToan/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE.docx
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

# HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE

**HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE**

1. ***

1. ; Giao dịch &gt; Đơn mua hàng &gt; + Mới.
2. sau:

- Phân loại PR/PO: **ZVOR**
- Ngành hàng: **Ô tô VF/Xe máy điện**
- Ngày yêu cầu giao hàng: **Theo nhu cầu cơ sở**
- Ưu tiên giao hàng VF: **Theo nhu cầu cơ sở**
- VF Kho: **Cơ sở điền với như sau:**

Ô tô VF: **4012**

Xe máy điện: **4011**

3. Trên thanh công cụ, nhấn nút **Lưu / Save** ghi.
4. **Đơn hàng mua,** mở tab **Chi tiết** xe cần đặt mua.
 - 4.1. !-- image -->

Điền vào các thông tin sau:

- **Mã sản phẩm**
- **Số lượng đặt (luôn 1)**
- **Configuration: cấu hình xe**
- **Manufacturing Year: năm sản xuất**
- **Mã kho: chọn kho VHC**

Bấm Lưu và tiếp :

- **Exterior Color: mã màu ngoại thất**
- **Interior Color: mã màu nội thất**

**Lưu ý: Đối với , cơ sở chỉ có thể tạo 1 dòng .**

- 4.2. điện

Điền vào các thông tin sau:

- **Mã sản phẩm/Product**
- **Số lượng đặt /Qty Order**
- **Mã kho/Warehouse: chọn kho VHC**

**Lưu ý: Đối với , cơ sở có thể tạo nhiều dòng chi tiết và số lượng nhiều xe ( tối đa 50 xe )**

**Sau khi điền , cơ sở bấm Lưu và bấm chọn nút Generate PO Detail:**

5. **Xe** sẽ hiển **** .
6. Trên thanh , nhấn **Điều khiển** và chọn status **Gửi.**
7. Trạng thái sẽ chuyển thành Đã xuống hệ thống SAP.
8. Cơ sở liên hệ Sales Admin ghép xe để sinh ra SO dưới SAP
9. thống SAP trả về Số đơn hàng SAP, thống DMS sẽ tự động chuyển sang trạng thái hành.

2. **Phiếu nhập kho xe**

Sau khi Sales Admin tạo thành công DO dưới SAP, phiếu đẩy lên DMS.

1. ; Giao dịch &gt; Phiếu nhập kho.
2. Màn hình **Phiếu nhập kho** hiện ra với **Phiếu nhập Kho** hiện có.
3. Tìm tới **Phiếu nhập Kho** của lọc theo mã lọc theo số phiếu giao (DO) phận phân phối gửi.
4. Double click để mở **.** Kiểm tra các thông tin, ví dụ:
 - **Mã phụ tùng / Product**
 - **Cấu hình xe ( đối với )**
 - **Số / Received Quantity**

5. Nhấn nút **Điều khiển** chọn *Phát hành* để xác nhận **Phiếu nhập kho.**