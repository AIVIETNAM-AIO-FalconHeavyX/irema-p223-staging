---
document_id: HUON426
title: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG
source_file: HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG.docx
source_path: Huong_dan_DMS/HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG.docx
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

# HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG

# Document Content

HƯỚNG DẪN TẠO ĐƠN MUA HÀNG PHỤ TÙNG

Tạo Đơn mua hàng là công việc chính của quy trình mua hàng.

Số lượng phụ tùng cần đặt mua trên Đơn mua hàng dựa vào nhu cầu tồn kho hoặc nhu cầu từ Lệnh sửa chữa hay Đơn đặt hàng từ khách hàng.

- Kiểm tra thông tin mã phụ tùng

- Vào Quản lý Tồn kho > Thiết lập thông tin Sản phẩm > Product List.

- Điền mã phụ tùng vào bộ lọc theo từ khóa

- Kiểm tra thông tin ngành hàng

Cơ sở double click vào bản ghi và kiểm tra ngành hàng:

- Kiểm tra bảng giá phụ tùng

- Vào Quản lý Mua > Thiết lập > Product List > Chi tiết bảng giá mua và chiết khấu.

- Điền mã phụ tùng vào bộ lọc theo từ khóa.

- Kiểm tra bảng giá

Trên bảng giá sẽ có cột Ngày bắt đầu hiệu lực và Giá mua:

- Tạo đơn mua hàng

- Vào Quản lý Mua > Giao dịch > Đơn mua hàng > + Mới.

- Nhập vào các thông tin sau:

- Phân loại PR/PO: ZVOR

- Ngành hàng: Phụ tùng Ô tô VF/Phụ tùng xe máy điện

- Ưu tiên giao hàng VF: Theo nhu cầu cơ sở

Lưu ý với mức độ ưu tiên VOR/Khẩn cấp, cơ sở cần điền mã lệnh sửa chữa vào đơn hàng. Hệ thống sẽ tự động lấy tất cả các dòng phụ tùng trong chi tiết lệnh sửa chữa vào chi tiết đơn đặt hàng.

Cơ sở có quyền chỉnh sửa số lượng phụ tùng và xóa dòng phụ tùng, tuy nhiên không thể tự thêm dòng:

- VF Kho/VF Sloc: Hệ thống sẽ tự điền với logic như sau:

Các SR/ĐL khu vực miền Bắc: chỉ mở kho 4013/1001

Các SR/ĐL khu vực miền Trung: chỉ mở kho 4013/1103

Các SR/ĐL khu vực miền Nam: chỉ mở kho 4013/1010

- Trường hợp, hệ thống không tự điền VF Kho/VF Sloc, cơ sở vui lòng tự điền theo logic bên trên.

- Trên thanh công cụ, nhấn nút Lưu / Save để lưu lại bản ghi.

- Sau khi lưu thông tin Đơn hàng mua, mở tab Chi tiết đơn hàng mua để nhập vào các mã Phụ tùng cần đặt mua (hướng dẫn ở bước 5).

- Hoặc nhấn nút MỚI phía trên lưới data để tạo mới hoặc nhấn nút Chi tiết đơn hàng / Add PO lines trên menu để tạo nhanh.

- Màn hình tạo Chi tiết đơn hàng mua hiển thị:

Điền vào các thông tin sau:

- Mã sản phẩm

- Số lượng đặt

- Trên thanh công cụ, nhấn nút Lưu để lưu lại bản ghi.

- Danh mục Phụ tùng sẽ được hiển thị trên lưới data trong màn hình Chi tiết / Detail đơn Mua hàng.

- Trên thanh tiêu đề, nhấn Điều khiển và chọn status Gửi.

- Trạng thái Đơn hàng sẽ chuyển thành Đã gửi và gửi thông tin xuống hệ thống SAP.

- Sau khi hệ thống SAP trả về Số đơn hàng SAP, đơn mua hàng trên hệ thống DMS sẽ tự động chuyển sang trạng thái Phát hành.

- Phiếu nhập kho

Cơ sở gửi số đơn hàng SAP cho bộ phận phân phối. Sau khi bộ phận phân phối hoàn thành dưới SAP, phiếu nhập kho sẽ được đẩy lên DMS.

- Vào Quản lý Mua > Giao dịch > Phiếu nhập kho.

- Màn hình Phiếu nhập kho hiện ra với danh mục các Phiếu nhập Kho hiện có.

- Tìm tới Phiếu nhập Kho của đơn hàng bằng cách lọc theo mã đơn đặt mua hàng hoặc lọc theo số phiếu giao (DO) mà bộ phận phân phối gửi.

- Double click để mở Phiếu nhập Kho. Kiểm tra các thông tin, ví dụ:

- Mã phụ tùng / Product

- Số lượng nhập kho / Received Quantity

- Nhấn nút Điều khiển chọn Phát hành để xác nhận Phiếu nhập kho.