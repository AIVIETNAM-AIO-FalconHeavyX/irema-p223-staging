---
document_id: HUON435
title: HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE
source_file: HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE.docx
source_path: Huong_dan_DMS/HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE.docx
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

# HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE

# Document Content

HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE VÀ CÁC LỖI THƯỜNG GẶP

Trường hợp Khách hàng có nhu cầu mua PIN, cơ sở cần thực hiện tạo đơn hàng PO đặt PIN kèm xe.

- Kiểm tra trạng thái PIN

- Vào Quản lý tồn kho xe -> Có liên quan -> Số sê – ri tồn kho:

- Kiểm tra trạng thái PIN

Cơ sở phải chắc chắc trạng thái PIN như sau:

Tình trạng tồn kho: Consignment

Tình trạng sẵn có: Có sẵn / Available

- Tạo đơn đặt hàng PO cho PIN kèm xe

- Vào Quản lý tồn kho -> Đơn đặt hàng -> + Mới

- Tạo đơn PO đặt PIN

Phân loại PR/PO: ZACI

Ngành hàng: Battery

VF Kho: 4011 (PIN XMĐ)

4012 (PIN Ô tô)

VF Sloc: 4001

Ưu tiên giao hàng VF: Cơ sở tự chọn theo mức độ ưu tiên

- Tạo chi tiết đơn PO đặt PIN

Tại phần chi tiết đặt hàng, cơ sở sẽ điền số tồn kho xe (số khung xe) -> hệ thống sẽ tự load ra thông tin PIN.

- Cơ sở thao tác gửi đơn hàng

Sau khi gửi đơn hàng thành công, cơ sở liên hệ Kế toán VF và Sales Admin thực hiện quy trình dưới SAP.

Chỉ khi Kế toán VF bỏ chặn payment dưới SAP, SAP mới đẩy thông tin SO lên DMS, đồng thời chuyển trạng thái đơn PO trên DMS lên hoàn thành và chuyển trạng thái PIN sang Tồn kho/Có sẵn. Cơ sở vui lòng liên hệ Kế toán VF phụ trách trước khi liên hệ IT.

- Các lỗi thường gặp

- Liên quan đến trạng thái PIN

IT ghi nhận rất nhiều trường hợp cơ sở tạo PO đặt PIN kèm xe lỗi như sau:

TH1.

Tình trạng tồn kho: Tồn kho

Tình trạng sẵn có: Có sẵn

Trường hợp này cơ sở đã đặt PIN thành công, cơ sở có thể kiểm tra đơn đặt PIN tại mục Battery Purchase Order ngay trên số sê - ri tồn kho PIN:

TH2.

Tình trạng tồn kho: Kế hoạch nhận

Tình trạng sẵn có: Không có sẵn

Trường hợp này, cơ sở cần kiểm tra lại xem đã phát hành phiếu nhập kho xe hay chưa. Logic: Sau khi phát hành phiếu nhập kho xe -> hệ thống sẽ tự phát hành số điều chỉnh tồn kho PIN và chuyển trạng thái PIN sang Consignment/Có sẵn:

- Không nhận được SO, DO sau khi submit PO PIN

Lỗi này liên quan đến đầu SAP và cần IT SAP xử lý. Do đó để tránh việc ticket bị xử lý lâu và không đúng nguồn, các cơ sở gửi mail cho IT SAP () theo tiêu đề: [SAP]_Mã cơ sở_Yêu cầu….