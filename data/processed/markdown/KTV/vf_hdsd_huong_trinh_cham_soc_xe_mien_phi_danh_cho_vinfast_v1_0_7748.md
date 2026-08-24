---
document_id: KTV001
title: VF HDSD HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0 7748
source_file: VF_HDSD_HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0_7748.docx
source_path: KTV/VF_HDSD_HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0_7748.docx
document_type: docx
role: technician
category: KTV
access_scope:
- technician
language: vi
version: '1.0'
pages: 1
pii_processed: true
pii_removed: true
processed_at: '2026-08-10'
---

# VF HDSD HƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ DÀNH CHO VINFAST V1.0 7748

**TÀI LIỆU HƯỚNG DẪN SỬ DỤNG DMS**

**CHƯƠNG TRÌNH CHĂM SÓC XE MIỄN PHÍ TẠI XDV XMĐ**

| Mã | VF-DMS-HDSD-VALET-001 |
|-----------------|-------------------------------------|
| Phiên bản | v0.1 |
| Ngày tạo | 16/07/2026 |
| Trạng thái | Publised |
| Phân loại | – Tài liệu hướng |
| Người soạn thảo | Trịnh Thị Thúy Nga (Ngattt30) |

## I. Quản lý Phiên bản Tài liệu

| **Phiên bản** | **Ngày tạo** | **Mô tả thay đổi** | **Người tạo** | **Trạng thái** |
|-----------------|----------------|----------------------|-----------------|------------------|
| v0.1 | 16/07/2026 | | Ngattt30 | Draft |
| v1.0 | | Ban hành chính thức | | |

## II. Phê duyệt Tài liệu

| **Vai trò** | **Họ tên** | **Chữ ký** | **Ngày** |
|-----------------|--------------------|--------------|------------|
| Người soạn thảo | Trịnh Thị Thúy Nga | | 16/07/2026 |
| kiểm tra | | | |
| Người phê duyệt | | | |

## III. Mục tiêu &amp; Phạm vi Tài liệu

### 3.1. Mục tiêu

Tài liệu này hướng dẫn nhận sự tại ĐLPP thực áp :

- Phát hành voucher áp dụng trên lệnh sửa chữa
- Claim hồ sơ Evoucher sau khi áp dụng

### 3.2. Phạm vi áp dụng

- Hệ thống: DMS – Phân hệ Dịch vụ sửa chữa
- Người dùng: CHT, KTV
- Phạm vi: nhánh (BU) thống DMS

### 3.3. Đối tượng đọc **Đối tượng** | **Vai trò** | **Mức độ đọc** |
|-----------------|-----------------------------|------------------|
| CHT NPP | Thực hiện trên DMS | **Bắt buộc** |
| KTV NPP | Thực hiện trên DMS | **Bắt buộc** |
| Bộ phận IT VH | Hỗ trợ kỹ thuật / cấu hình | **Bắt buộc** |

## IV. Thuật ngữ &amp; Từ viết tắt

| **#** | **Từ viết tắt** | **Mô tả** |
|---------|-------------------|----------------------------------------------------|
| 1 | **DMS** | Dealer Management System – Hệ thống quản lý đại lý |
| 2 | **BU** | Business Unit – Chi nhánh / Đơn vị kinh doanh |
| 3 | ĐLPP | Đại lý phân phối |
| 4 | **CHT** | Cửa hàng trưởng |
| 5 | **KTV** | Kĩ thuật viên |
| 6 | **KH** | Khách hàng |
| 7 | **ĐKX** | kí xe |

## V. Tài liệu Liên quan

| **#** | *** | **Mô tả** | **Phiên bản** | **Ghi chú** |
|---------|--------------------|-------------|-----------------|---------------|
| 1 | | | | |
| 2 | | | | |

## VI. Tổng quan Chức năng

Chức năng cho phép ĐLPP thực hiện phát hành voucher cho XMĐ và claim hồ sơ Evoucher sau khi áp thống DMS.

### 6.1. nghiệp vụ tổng quát

| **#** | **Bước** | **Mô tả** | **Người thực hiện** | **Hệ thống** |
|---------|------------------------------------|---------------------------------------------------------|-----------------------|----------------|
| 1 | **Tiếp nhận yêu cầu** | KH liên hệ qua ĐLPP tin kí xe | ĐLPP / KH | DMS |
| 2 | **Sử dụng voucher trên phiếu thu** | CHT/KTV thực hiện mở lệnh sửa chữa và áp dụng | KTV/CHT | DMS / Loyalty |
| 3 | **Submit hồ sơ Evoucher** | CHT/KTV thu thập giấy tờ hồ sơ sơ claim Evoucher | KTV/CHT | DMS |

### 6.2. Sơ đồ trạng thái (Status Flow)

| **Trạng thái** | **Mô tả** | **Chuyển sang** | **Điều kiện** |
|------------------|--------------------|-------------------|----------------------------------------|
| **Open** | Yêu cầu mới tạo | | |
| **Release** | ** | hành phiếu thu voucher thành công |

## VII. ### 7.1. dụng voucher trên Lệnh sửa chữa qua phiếu thu

**Người thực hiện:** CHT/KTV

**:** Lệnh sửa chữa ở trạng thái Lệnh sửa chữa/ toán

**⚠ Lưu ý:**

- Mỗi voucher redeem 1 lần
- VIN xe sửa chữa số VIN đã được cấp phát voucher thì mới redeem được thành công.

Người dùng chọn  toán =&gt; Chọn phiếu thu =&gt; , thực hiện Trả trước

- Tiền đặt cọc: Không

- Mã khách hàng

- Tiền mặt và NH: 9

- Phương thức thanh toán: 9

Sau khi save, thực hiện tạo tổng quan phiếu thu thành công.

Sau khi tạo xong tổng quan, người dùng thực hiện  giao  phiếu thu:

Người dùng thực hiện  nguồn:  lệnh sửa chữa: Mã WO có đúng  cần redeem voucher

- **Mã voucher: VCTAXMD2026600 (Mã voucher sẽ dùng chung cho tất cả các XMĐ đủ điều kiện )**

Người dùng thực hiện lưu phiếu  tiết.

Sau khi tạo xong phiếu  tiết, người dùng thực hiện phát hành phiếu thu để redeem voucher cho  sửa chữa này.  hành thành công, trạng thái phiếu thu chuyển sang hành và cập nhật đã   thành công.

### 7.2. Claim sửa chữa

**Người thực hiện:** CHT/KTV

**⚠ Lưu ý:**

- Chỉ tạo Evoucher Transaction cho các lệnh sửa chữa ở trạng thái Hoàn thành thanh toán (Invoice) hoặc Hoàn thành (Completed)
- Mỗi lệnh sửa chữa claim 1 lần Evoucher Transaction, trường hợp người dùng thu thêm phiếu thu voucher 9 thì vui lòng cancel Evoucher Transaction đã ghi khác.
- Khi đã tạo mới Evoucher Transaction, người dùng không được phép hủy phiếu thu voucher (Payment 9). , bắt buộc phải hủy Evoucher Transaction trước khi tạo phiếu thu hủy.

Bước 1: (Evoucher Transaction)

Người dùng truy cập vào tab “ sửa chữa” =&gt; Chọn “Evoucher Transaction” =&gt; bấm “ (New)”

Màn hình hiển thị tạo mới bản ghi, người dùng điền thông tin mã lệnh sửa chữa cần claim và bấm lưu (Save)

Hệ thống tự động load ra  thông tin như sau:

- Mã lệnh sửa chữa (WO)

- Số khung xe (VIN)

- Mã voucher/Voucher code: Đã redeem  phiếu thu của lệnh

- Số tiền voucher/ Voucher Amount: Tổng tiền voucher  phiếu thu

- Số tiền khách hàng thanh toán LSC/Work Order Amount

- Số tiền thanh toán Voucher chia 2 TH như sau:

- Tiền voucher &gt; tổng  WO =&gt; Số Tiền thanh toán voucher =  WO

- Tiền voucher &lt;  tiền  WO =&gt; Số Tiền thanh toán voucher = Tiền voucher

Sau khi lấy ra lệnh sửa chữa, hệ thống sẽ tính toán ra tổng tiền của bản ghi đó:

- Tổng tiền KH thanh toán LSC/Total Work Order Amount

- Tổng tiền Voucher/Total Voucher Amount

- Tổng tiền thanh toán Voucher/Total Payment Amount

Bước 2: Đính kèm giấy tờ lên hồ sơ Evoucher

Sau khi tạo mới và check , đính kèm 4 loại giấy tờ sau lên DMS:

- Quyết toán sửa chữa (Decided to repair file)

- Hóa đơn xuất cho khách hàng (Invoice issued to customer file)

- Giấy đăng kí xe (Vehicle registration file)

- Phiếu xác nhận voucher (Voucher file confirmation form)

**⚠ Lưu ý: Đính kèm file dưới dạng .PDF hoặc hình ảnh**

Sau khi add đủ 4 loại giấy tờ hệ thống gửi phê duyệt đến Nhóm hỗ trợ hậu mãi phê duyệt hồ sơ.

Bước 3: Phê duyệt hồ sơ Evoucher Transaction

Tại bản ghi đã tạo mới và add hồ sơ thành công, chọn điều khiển/ handling = Send For Approval và Lưu để gửi đi

Trạng thái bản ghi chuyển sang On Approval/Chờ phê duyệt

Người dùng liên hệ Nhóm hỗ trợ hậu mãi phê duyệt hồ sơ claim. , Trạng thái bản ghi chuyển sang Phê duyệt/Approved và tự động update :

- Người phê duyệt/Approver

- Ngày phê duyệt/Approval Date

Cuối tháng Bộ phận hỗ trợ hậu mãi sẽ thực hiện tổng sơ Evoucher đã được thực hiện Evoucher Transaction Submission.

## VIII. Sự cố &amp; Câu hỏi Thường gặp (FAQ)

| **#** | **Vấn đề** | **Nguyên nhân có thể** | **Hướng xử lý** |
|---------|--------------|--------------------------|-------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

***— Kết thúc sóc xe miễn phí tại XDV—***