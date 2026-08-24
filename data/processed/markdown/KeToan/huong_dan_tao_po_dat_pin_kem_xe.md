---
document_id: KETO756
title: HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE
source_file: HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE.docx
source_path: KeToan/HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE.docx
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

# HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE

**HƯỚNG DẪN TẠO PO ĐẶT PIN KÈM XE THƯỜNG GẶP**

Trường hợp Khách hàng có nhu cầu mua PIN, cơ sở cần thực hiện tạo đơn hàng PO đặt PIN kèm xe.

1. **Kiểm tra trạng thái PIN**

1. ** tồn ; ; – ri tồn kho:**
2. **Kiểm tra trạng thái PIN**

Cơ sở thái PIN như sau:

**Tình trạng tồn kho** : Consignment

**Tình trạng sẵn có** : Có sẵn / Available

2. ** kèm xe**

1. ** tồn kho -&gt; ; + Mới**
2. **Tạo đơn PO đặt PIN**

**Phân loại PR/PO** : ZACI

**Ngành hàng** : Battery

**VF Kho** : 4011 (PIN XMĐ)

4012 (PIN Ô tô)

**VF Sloc** : 4001

**Ưu tiên giao hàng VF** : Cơ sở tự chọn theo mức độ ưu tiên

3. ****

Tại phần , cơ sở sẽ điền số tồn kho xe (số khung xe) -&gt; hệ thống sẽ tự load ra tin PIN.

4. **Cơ sở **

, cơ sở liên hệ Kế toán VF và Sales Admin thực .

 Kế toán VF bỏ chặn payment dưới SAP, SAP mới đẩy thông tin SO , đồng thời chuyển trạng thái trên DMS lên hoàn trạng thái PIN sang **Tồn kho/Có sẵn** . Cơ sở toán VF phụ trách trước IT.

3. ** lỗi thường gặp**

1. ** đến trạng thái PIN**

IT ghi nhận rất nhiều trường hợp cơ sở tạo PO đặt PIN kèm xe lỗi như sau:

**TH1.**

**Tình trạng tồn kho** : Tồn kho

**Tình trạng sẵn có** : Có sẵn

Trường hợp này cơ sở đã đặt PIN thành công, cơ sở có thể kiểm tra đơn đặt PIN tại mục Battery Purchase Order tồn kho PIN:

**TH2.**

**Tình trạng tồn kho** : Kế hoạch nhận

**Tình trạng sẵn có** : Không có sẵn

, cơ sở cần kiểm tra lại xem đã phát hành phiếu . Logic: hành phiếu ; hệ thống số điều chỉnh tồn kho PIN và chuyển trạng thái PIN sang Consignment/Có sẵn:

2. **Không nhận được SO, DO submit PO PIN**

Lỗi này liên quan đến đầu IT SAP xử lý. Do tránh việc ticket , các cơ sở gửi mail cho IT SAP ( [](mailto:) ) : [SAP]\_Mã cơ sở\_Yêu cầu….