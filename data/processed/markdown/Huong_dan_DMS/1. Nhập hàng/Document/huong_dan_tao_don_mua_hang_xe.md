---
document_id: HUON462
title: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE
source_file: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE.docx
source_path: Huong_dan_DMS/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE.docx
document_type: docx
role: general
category: Huong_dan_DMS
access_scope:
- accounting
- sales
- technician
- owner
- general
language: vi
version: '1.0'
pages: 1
pii_processed: true
pii_removed: true
processed_at: '2026-08-22'
---

# HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE

# Document Content

HƯỚNG DẪN TẠO ĐƠN MUA HÀNG XE

- Tạo đơn mua hàng xe

- Vào Quản lý Mua > Giao dịch > Đơn mua hàng > + Mới.

- Nhập vào các thông tin sau:

- Phân loại PR/PO: ZVOR

- Ngành hàng: Ô tô VF/Xe máy điện

- Ngày yêu cầu giao hàng: Theo nhu cầu cơ sở

- Ưu tiên giao hàng VF: Theo nhu cầu cơ sở

- VF Kho: Cơ sở điền với thông tin như sau:

Ô tô VF: 4012

Xe máy điện: 4011

- Trên thanh công cụ, nhấn nút Lưu / Save để lưu lại bản ghi.

- Sau khi lưu thông tin Đơn hàng mua, mở tab Chi tiết đơn hàng mua để nhập thông tin xe cần đặt mua.

- Tạo chi tiết đơn hàng đặt Ô tô VF

Điền vào các thông tin sau:

- Mã sản phẩm

- Số lượng đặt (luôn luôn để là 1)

- Configuration: cấu hình xe

- Manufacturing Year: năm sản xuất

- Mã kho: chọn kho VHC

Bấm Lưu và tiếp tục điền các thông tin:

- Exterior Color: mã màu ngoại thất

- Interior Color: mã màu nội thất

Lưu ý: Đối với đơn đặt Ô tô VF, cơ sở chỉ có thể tạo 1 dòng chi tiết và cho 1 xe.

- Tạo chi tiết đơn hàng đặt Xe máy điện

Điền vào các thông tin sau:

- Mã sản phẩm/Product

- Số lượng đặt /Qty Order

- Mã kho/Warehouse: chọn kho VHC

Lưu ý: Đối với đơn đặt Xe máy điện, cơ sở có thể tạo nhiều dòng chi tiết và số lượng nhiều xe ( tối đa 50 xe )

Sau khi điền thông tin, cơ sở bấm Lưu và bấm chọn nút Generate PO Detail:

- Danh mục Xe sẽ được hiển thị trên lưới data trong màn hình Chi tiết / Detail đơn Mua hàng.

- Trên thanh tiêu đề, nhấn Điều khiển và chọn status Gửi.

- Trạng thái Đơn hàng sẽ chuyển thành Đã gửi và gửi thông tin xuống hệ thống SAP.

- Cơ sở liên hệ Sales Admin ghép xe để sinh ra số đơn hàng SO dưới SAP

- Sau khi hệ thống SAP trả về Số đơn hàng SAP, đơn mua hàng trên hệ thống DMS sẽ tự động chuyển sang trạng thái Phát hành.

- Phiếu nhập kho xe

Sau khi Sales Admin tạo thành công DO dưới SAP, phiếu nhập kho sẽ được đẩy lên DMS.

- Vào Quản lý Mua > Giao dịch > Phiếu nhập kho.

- Màn hình Phiếu nhập kho hiện ra với danh mục các Phiếu nhập Kho hiện có.

- Tìm tới Phiếu nhập Kho của đơn hàng bằng cách lọc theo mã đơn đặt mua hàng hoặc lọc theo số phiếu giao (DO) mà bộ phận phân phối gửi.

- Double click để mở Phiếu nhập Kho. Kiểm tra các thông tin, ví dụ:

- Mã phụ tùng / Product

- Cấu hình xe ( đối với đơn đặt Ô tô VF )

- Số lượng nhập kho / Received Quantity

- Nhấn nút Điều khiển chọn Phát hành để xác nhận Phiếu nhập kho.