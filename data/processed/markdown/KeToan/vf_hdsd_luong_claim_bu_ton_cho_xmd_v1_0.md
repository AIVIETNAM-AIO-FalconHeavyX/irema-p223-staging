---
document_id: KETO001
title: VF HDSD Luồng claim bù tồn cho XMĐ v1.0
source_file: VF_HDSD_Luồng claim bù tồn cho XMĐ v1.0.docx
source_path: KeToan/VF_HDSD_Luồng claim bù tồn cho XMĐ v1.0.docx
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

# VF HDSD Luồng claim bù tồn cho XMĐ v1.0

**TÀI LIỆU HƯỚNG DẪN SỬ DỤNG DMS**

**LUỒNG HỒ SƠ CLAIM BÙ TỒN CHO XE MÁY ĐIỆN**

| Mã | VF-DMS-HDSD-VALET-001 |
|-----------------|-------------------------------------|
| Phiên bản | V1.0 |
| Ngày tạo | 04/08/2026 |
| Trạng thái | Publised |
| Phân loại | – Tài liệu hướng |
| Người soạn thảo | Trịnh Thị Thúy Nga (Ngattt30) |

## I. Quản lý Phiên bản Tài liệu

| **Phiên bản** | **Ngày tạo** | **Mô tả thay đổi** | **Người tạo** | **Trạng thái** |
|-----------------|----------------|----------------------|-----------------|------------------|
| v0.1 | 04/08/2026 | | Ngattt30 | Draft |
| v1.0 | | Ban hành chính thức | | |

## II. Phê duyệt Tài liệu

| **Vai trò** | **Họ tên** | **Chữ ký** | **Ngày** |
|-----------------|--------------------|--------------|------------|
| Người soạn thảo | Trịnh Thị Thúy Nga | | 04/08/2026 |
| kiểm tra | | | |
| Người phê duyệt | | | |

## III. Mục tiêu &amp; Phạm vi Tài liệu

### 3.1. Mục tiêu

Tài liệu này hướng dẫn nhận sự tại ĐLPP thực claim hồ sơ XMĐ đối với nghiệp vụ claim bù tồn đối với các xe có thay ### 3.2. Phạm vi áp dụng

- Hệ thống: DMS – Phân hệ Kinh Doanh
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

Chức năng cho phép ĐLPP thực hiện claim bù tồn chênh lệch sỉ xe XMĐ.

### 6.1. nghiệp vụ tổng quát

| **#** | **Bước** | **Mô tả** | **Người thực hiện** | **Hệ thống** |
|---------|---------------------------------------------------|------------------------------------------------------------------------|-----------------------|----------------|
| 1 | ** bù tồn lên DMS** | VHKD thực bù DMS cho từng số khung xe | VHKD | DMS |
| 2 | **Kế toán phê duyệt bảng giá bù tồn trên DMS** | VHKD gửi kế toán phê duyệt bảng giám bù | KT | DMS |
| 3 | **NPP thực hiện làm hồ sơ claim bù tồn trên DMS** | CHT tạo hồ sơ claim claim khoản bù số khung xe | CHT | DMS |

### 6.2. Sơ đồ trạng thái (Status Flow)

| **Trạng thái** | **Mô tả** | **Chuyển sang** | **Điều kiện** |
|------------------|--------------------------------|-------------------|-----------------|
| **Open** | Yêu cầu mới tạo | | |
| Waiting | Chờ VHKD phê duyệt hồ sơ claim | **SAP Approved** | |

## VII. ### 7.1. tổng sơ claim cho XMĐ

**Người thực hiện:** CHT

**Áp dụng:** cho các trường hợp số khung xe có thay lẻ đối với xe toán đã phê duyệt giá bù dùng chọn Kế toán/Cashier =&gt; Chọn Dealer Claim Payment =&gt; Bấm New/Tạo mới

 bấm , màn hình hiển thị giao diện hồ sơ claim, chọn :

- Bussiness Unit: Mã chi nhánh
- Transaction Date/Ngày giao dịch
- Type/Loại: Offset Debt/Cấn trừ công nợ
- Claim Source: Inventory New Vehicle (Xe tồn kho)
- Ngành hàng/VF Division: Xe máy điện/ to: dùng thực hiện chọn 1 trong 2 lựa chọn sau:
 - Trading: Khi thực hiện claim cho số khung xe (Theo PO nhập xe)
 - Newco: Khi thực hiện claim cho số khung xe nhập từ Newco (Theo PO nhập xe)

, hệ thống sinh ra bản ghi tổng sơ claim cho NPP:

### 7.2. sơ claim cho số khung xe cần claim bù tồn

**Người thực hiện:** CHT

**⚠ Lưu ý:**

- Người dùng chỉ claim chênh lệch sỉ cho xe được kinh doanh đã tính toán xong tiền hồ sơ claim, đẩy lên hệ thống DMS toán đã phê duyệt bảng khoản bù 1 khoảng claim trên 1 hồ sơ claim.

Người dùng chọn tab Claim Details ( sơ claim) =&gt; Bấm tạo mới Dealer Claim Payment Details sau đó điền thông tin số tồn kho xe cần claim chênh lệch sỉ

Người dùng nhập số khung xe vào Invetory New Vehicle =&gt; /Save=&gt; Hệ thống tự động lấy ra khoản tiền chênh lệch sỉ đã được .

Người dùng muốn claim tiền bù nhiêu xe thì tạo bấy nhiêu chi tiết tương ứng cho hồ sơ claim

Sau khi tạo chi tiết thành công, hệ thống tự động cộng tổng bù tồn cơ sở được claim ra tổng sơ claim.

**Người dùng tra cứu giá chênh lệch sỉ (bù tồn) số khung xe tại bảng Cashier/Kế toán =&gt; Chọn bảng Wholesale Priced Difference Config. được thì mới claim chênh lệch sỉ cho xe trước bán thành công.**

### 7.3. Đính kèm tài liệu trên hồ sơ claim

Người dùng chọn mục Attachment File để đính kèm hồ sơ giấy tờ VHKD phê duyệt

Sau khi chọn file =&gt; <!-- image -->

### 7.4. Gửi duyệt hồ sơ claim bù tồn và đẩy sang SAP

Sau khi tạo đầy đủ các xe cần claim bù tồn và đính , lên Vận hành Kinh Doanh: Chọn Điều khiển = Send for Approve =&gt; Bấm Lưu/Save

Hồ sơ claim chuyển sang trạng thái Waiting HO

 Vận hành kinh , claim tự động đẩy sang SAP =&gt; Trạng thái hồ sơ claim chuyển sang Waiting SAP

 phê duyệt hồ sơ claim dưới SAP, trạng thái trên DMS chuyển sang SAP Approved

**⚠ Lưu ý:**

- Trường hợp kế toán reject dưới SAP, trạng thái hồ sơ claim trên DMS chuyển thành SAP Rejected, reopen lại hồ sơ claim và chỉnh sửa thông tin cần thiết sau đó gửi phê duyệt lại từ đầu.
- Người dùng kiểm tra lý do từ chối/Reject Reason của sơ claim

## VIII. Sự cố &amp; Câu hỏi Thường gặp (FAQ)

| **#** | **Vấn đề** | **Nguyên nhân có thể** | **Hướng xử lý** |
|---------|--------------|--------------------------|-------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

***— Kết thúc sơ claim bù tồn cho XMĐ—***