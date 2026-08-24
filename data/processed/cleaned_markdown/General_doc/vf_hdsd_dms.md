---
document_id: GENE163
title: VF HDSD DMS
source_file: VF_HDSD_DMS.docx
source_path: General_doc/VF_HDSD_DMS.docx
document_type: docx
role: general
category: General_doc
access_scope:
- accounting
- sales
- technician
language: vi
version: '1.0'
pages: 1
pii_processed: true
pii_removed: true
processed_at: '2026-08-13'
---

# VF HDSD DMS

# Document Content

TÀI LIỆU HƯỚNG DẪN SỬ DỤNG DMS

CHƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ TẠI XDV XMĐ

| Mã tài liệu | VF-DMS-HDSD-VALET-001 |
| --- | --- |
| Phiên bản | v0.1 |
| Ngày tạo | 16/07/2026 |
| Trạng thái | Publised |
| Phân loại | Nội bộ – Tài liệu hướng dẫn sử dụng |
| Người soạn thảo | Trịnh Thị Thúy Nga (Ngattt30) |

# I. Quản lý Phiên bản Tài liệu

| Phiên bản | Ngày tạo | Mô tả thay đổi | Người tạo | Trạng thái |
| --- | --- | --- | --- | --- |
| v0.1 | 16/07/2026 | Tạo mới tài liệu | Ngattt30 | Draft |
| v1.0 | | Ban hành chính thức | | |

# II. Phê duyệt Tài liệu

| Vai trò | Họ tên | Chữ ký | Ngày |
| --- | --- | --- | --- |
| Người soạn thảo | Trịnh Thị Thúy Nga | | 16/07/2026 |
| Người kiểm tra | | | |
| Người phê duyệt | | | |

## 3.1. Mục tiêu

Tài liệu này hướng dẫn nhận sự tại ĐLPP thực hiện quy trình áp dụng voucher chăm sóc xe miễn phí bao gồm:

- Phát hành voucher áp dụng trên lệnh sửa chữa

- Claim hồ sơ Evoucher sau khi áp dụng

## 3.2. Phạm vi áp dụng

- Hệ thống: DMS – Phân hệ Dịch vụ sửa chữa

- Người dùng: CHT, KTV

- Phạm vi: Tất cả các chi nhánh (BU) sử dụng hệ thống DMS

## 3.3. Đối tượng đọc tài liệu

| Đối tượng | Vai trò | Mức độ đọc |
| --- | --- | --- |
| CHT NPP | Thực hiện thao tác trên DMS | Bắt buộc |
| KTV NPP | Thực hiện thao tác trên DMS | Bắt buộc |
| Bộ phận IT VH | Hỗ trợ kỹ thuật / cấu hình | Bắt buộc |

# IV. Thuật ngữ & Từ viết tắt

| # | Từ viết tắt | Mô tả |
| --- | --- | --- |
| 1 | DMS | Dealer Management System – Hệ thống quản lý đại lý |
| 2 | BU | Business Unit – Chi nhánh / Đơn vị kinh doanh |
| 3 | ĐLPP | Đại lý phân phối |
| 4 | CHT | Cửa hàng trưởng |
| 5 | KTV | Kĩ thuật viên |
| 6 | KH | Khách hàng |
| 7 | ĐKX | Đăng kí xe |

# V. Tài liệu Liên quan

| # | Tên tài liệu | Mô tả | Phiên bản | Ghi chú |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |

# VI. Tổng quan Chức năng

Chức năng cho phép ĐLPP thực hiện phát hành voucher cho XMĐ và claim hồ sơ Evoucher sau khi áp dụng trên hệ thống DMS.

## 6.1. Luồng nghiệp vụ tổng quát

| # | Bước | Mô tả | Người thực hiện | Hệ thống |
| --- | --- | --- | --- | --- |
| 1 | Tiếp nhận yêu cầu | KH liên hệ qua ĐLPP cung cấp thông tin Đăng kí xe | ĐLPP / KH | DMS |
| 2 | Sử dụng voucher trên phiếu thu | CHT/KTV thực hiện mở lệnh sửa chữa và áp dụng | KTV/CHT | DMS / Loyalty |
| 3 | Submit hồ sơ Evoucher | CHT/KTV thu thập giấy tờ hồ sơ tạo hồ sơ claim Evoucher | KTV/CHT | DMS |

## 6.2. Sơ đồ trạng thái (Status Flow)

| Trạng thái | Mô tả | Chuyển sang | Điều kiện |
| --- | --- | --- | --- |
| Open | Yêu cầu mới tạo | | |
| Release | Áp dụng chính sách | Release | Phát hành phiếu thu voucher thành công |

## 7.1. Sử dụng voucher trên Lệnh sửa chữa qua phiếu thu

Người thực hiện: CHT/KTV

Áp dụng khi: Lệnh sửa chữa ở trạng thái Lệnh sửa chữa/Quyết toán

⚠ Lưu ý:

- Mỗi voucher chỉ được redeem 1 lần

- VIN xe trên lệnh sửa chữa phải khớp với số VIN đã được cấp phát voucher thì mới redeem được thành công.

Người dùng chọn mục Kế toán => Chọn phiếu thu => Bấm tạo mới, thực hiện nhập các thông tin sau:

- Loại: Trả trước

- Tiền đặt cọc: Không

- Mã khách hàng

- Tiền mặt và NH: 9

- Phương thức thanh toán: 9

Sau khi save, thực hiện tạo tổng quan phiếu thu thành công.

Sau khi tạo xong tổng quan, người dùng thực hiện tạo chi tiết giao dịch để tạo mới chi tiết phiếu thu:

Người dùng thực hiện nhập các thông tin sau:

- Loại nguồn: Dịch vụ

- Mã lệnh sửa chữa: Mã WO có đúng số VIN cần redeem voucher

- Mã voucher: VCTAXMD2026600 (Mã voucher sẽ dùng chung cho tất cả các XMĐ đủ điều kiện hưởng chương trình)

Người dùng thực hiện lưu phiếu thu chi tiết.

Sau khi tạo xong phiếu thu chi tiết, người dùng thực hiện phát hành phiếu thu để redeem voucher cho lệnh sửa chữa này. Sau khi phát hành thành công, trạng thái phiếu thu chuyển sang Phát hành và cập nhật đã sử dụng voucher thành công.

## 7.2. Claim Evoucher sau khi đã sử dụng qua lệnh sửa chữa

Người thực hiện: CHT/KTV

⚠ Lưu ý:

- Chỉ tạo Evoucher Transaction cho các lệnh sửa chữa ở trạng thái Hoàn thành thanh toán (Invoice) hoặc Hoàn thành (Completed)

- Mỗi lệnh sửa chữa chỉ được claim 1 lần Evoucher Transaction, trường hợp người dùng thu thêm phiếu thu voucher 9 thì vui lòng cancel Evoucher Transaction đã tạo và tạo mới lại bản ghi khác.

- Khi đã tạo mới Evoucher Transaction, người dùng không được phép hủy phiếu thu voucher (Payment 9). Trường hợp cần hủy, người dùng bắt buộc phải hủy Evoucher Transaction trước khi tạo phiếu thu hủy.

Bước 1: Tạo mới hồ sơ Evoucher (Evoucher Transaction)

Người dùng truy cập vào tab “Dịch vụ sửa chữa” => Chọn “Evoucher Transaction” => bấm “Tạo mới (New)”

Màn hình hiển thị tạo mới bản ghi, người dùng điền thông tin mã lệnh sửa chữa cần claim và bấm lưu (Save)

Hệ thống tự động load ra các thông tin như sau:

- Mã lệnh sửa chữa (WO)

- Số khung xe (VIN)

- Mã voucher/Voucher code: Đã redeem trên phiếu thu của lệnh

- Số tiền voucher/ Voucher Amount: Tổng tiền voucher trên phiếu thu

- Số tiền khách hàng thanh toán LSC/Work Order Amount

- Số tiền thanh toán Voucher chia 2 TH như sau:

- Tiền voucher > tổng tiền trên WO => Số Tiền thanh toán voucher = Grantotal WO

- Tiền voucher < Tổng tiền trên WO => Số Tiền thanh toán voucher = Tiền voucher

Sau khi lấy ra toàn bộ chi tiết của lệnh sửa chữa, hệ thống sẽ tính toán ra tổng tiền của bản ghi đó:

- Tổng tiền KH thanh toán LSC/Total Work Order Amount

- Tổng tiền Voucher/Total Voucher Amount

- Tổng tiền thanh toán Voucher/Total Payment Amount

Bước 2: Đính kèm giấy tờ lên hồ sơ Evoucher

Sau khi tạo mới và check thông tin đã đúng, người dùng thao tác đính kèm 4 loại giấy tờ sau lên DMS:

- Quyết toán sửa chữa (Decided to repair file)

- Hóa đơn xuất cho khách hàng (Invoice issued to customer file)

- Giấy đăng kí xe (Vehicle registration file)

- Phiếu xác nhận voucher (Voucher file confirmation form)

⚠ Lưu ý: Đính kèm file dưới dạng .PDF hoặc hình ảnh

Sau khi add đủ 4 loại giấy tờ hệ thống mới cho phép gửi phê duyệt đến Nhóm hỗ trợ hậu mãi để phê duyệt hồ sơ.

Bước 3: Phê duyệt hồ sơ Evoucher Transaction

Tại bản ghi đã tạo mới và add hồ sơ thành công, người dùng chọn điều khiển/ handling = Send For Approval và Lưu để gửi đi

Trạng thái bản ghi chuyển sang On Approval/Chờ phê duyệt

Người dùng liên hệ Nhóm hỗ trợ hậu mãi để phê duyệt hồ sơ claim. Sau khi phê duyệt thành công, Trạng thái bản ghi chuyển sang Phê duyệt/Approved và tự động update thông tin:

- Người phê duyệt/Approver

- Ngày phê duyệt/Approval Date

Cuối tháng Bộ phận hỗ trợ hậu mãi sẽ thực hiện tổng hợp các hồ sơ Evoucher đã được phê duyệt trong tháng để thực hiện Evoucher Transaction Submission.

# VIII. Xử lý Sự cố & Câu hỏi Thường gặp (FAQ)

| # | Vấn đề | Nguyên nhân có thể | Hướng xử lý |
| --- | --- | --- | --- |
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

— Kết thúc tài liệu hướng dẫn chương trình chăm sóc xe miễn phí tại XDV—