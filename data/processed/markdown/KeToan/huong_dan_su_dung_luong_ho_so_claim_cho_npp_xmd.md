---
document_id: KETO499
title: Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ
source_file: Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ.docx
source_path: KeToan/Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ.docx
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

# Hướng dẫn sử dụng luồng hồ sơ claim cho NPP XMĐ

**Hướng dẫn sử dụng luồng hồ sơ claim cho Xe Máy Điện**

########### Hồ sơ claim cho XMĐ

**1. claim tiền CTKM cho xe đã xuất hóa khách hàng cuối	2**

*a.	Tạo mới tổng sơ claim cho 2*

*b.	Tạo mới chi tiết hồ sơ claim cho 3*

*c.	Đính kèm tài liệu trên hồ sơ claim	6*

*d.	Gửi hồ sơ claim cho Vận Hành Kinh Doanh phê duyệt và đẩy SAP	7*

**2.	Cấn trừ công nợ PO sơ claim	10**

*a.	Tạo mới chi tiết đơn hàng PO cần cấn trừ công nợ sơ claim	10*

*b.	Đẩy thông tin PO cấn trừ sang SAP	11*

1. ** claim tiền CTKM cho xe đã xuất hóa khách hàng cuối**

Áp dụng cho các xe có các CTKM trừ thẳng vào giá xuất hóa (fix discount, job level discount, vinclub discount); quy phiếu thu 51 hoặc bù tồn ( được claim xe trước bán)

1. * tổng sơ claim cho NVSO*

Người dùng chọn toán/Cashier =&gt; Chọn Dealer Claim Payment =&gt; Bấm New/Tạo mới

 bấm , màn hình hiển thị giao diện hồ sơ claim, chọn :

- Bussiness Unit: Mã chi nhánh
- Transaction Date/Ngày giao dịch
- Type/Loại: Offset Debt/Cấn trừ công nợ
- Claim Source: NVSO (Đơn hàng bán xe)
- Ngành hàng/VF Division: Xe máy điện/ *Claim to (mới):** Người dùng thực hiện chọn 1 trong 2 lựa chọn sau:
 - **Trading** : Khi thực hiện claim cho hang VSO xuất bán cho xe nhập từ Trading (Theo PO nhập xe từ Kho/Plant 4011 )
 - **VFVN:** Khi thực hiện claim cho (Theo PO nhập xe từ Kho/Plant 4023)

**Lưu ý:**

- **Claim to về Trading hay VFVN phụ thuộc vào VIN xe NVSO được đặt hàng từ Trading hay VFVN, người dùng cần kiểm tra Xe của đơn hàng đó được đặt mua từ Trading/VFVN.**
- **Một hồ sơ Claim không add 2 đơn hàng/VSO thuộc 2 nguồn mua khác nhau. Do đó nếu cần Claim các đơn bán xe Trading/VFVN cần tạo 2 hồ sơ Claim độc lập**

2. * sơ claim cho

Người dùng chọn tab Claim Details ( sơ claim) =&gt; Bấm tạo mới Dealer Claim Payment Details sau đó điền tin đơn hàng bán xe (NVSO) cần claim

Người dùng nhập số đơn hàng bán xe (NVSO) vào NV Sale Order =&gt; /Save

, hệ thống tự động tính ra được claim (nếu có) bao gồm tiền CTKM gốc claim đã chiết NPP được hưởng:

- Tiền giảm giá CTKM (Fix discount)
- Tiền giảm giá cấp bậc CBNV (Job level discount)
- Tiền giảm giá claim (Thu theo phiếu thu 51)
- Tiền voucher (redeem voucher qua phiếu thu 34)
- Tiền chênh lệch sỉ/bù tồn (Trường hợp xe chưa claim chênh lệch sỉ/bù tồn thì lấy khoản claim theo NVSO)

 thống tổng :

- **Tiền KM trừ thẳng = Tiền giảm giá CTKM Claim + Tiền giảm giá CBNV Claim + Tiền giảm giá Vinclub Claim**
- **Quy đổi tiền mặt NVSO = claim + Tiền voucher claim**
- **Tổng tiền KM đơn hàng = Tiền KM trừ thẳng NVSO + Tiền chênh lệch sỉ NVSO**

NPP claim bao nhiêu đơn hàng thì tạo bấy nhiêu sơ claim. Hệ thống tự động tính tổng tiền NPP claim ở ngoài giao dịch claim tổng (Bao gồm tiền gốc được claim)

Lưu ý:

- Mỗi đơn hàng claim hồ sơ 1 lần, trạng thái phải là Invoice/Hóa đơn
- Mỗi xe claim chênh lệch sỉ 1 lần trong cùng 1 khoảng , nếu đã claim xe claim theo NVSO sẽ không có tiền chênh lệch sỉ
- **Số tiền NPP được claim cuối là giá ở cột Claim amount.**

3. *Đính kèm tài liệu trên hồ sơ claim*

Người dùng chọn mục Attachment File để đính kèm hồ sơ giấy tờ VHKD phê duyệt

Sau khi chọn file =&gt; <!-- image -->

4. *Gửi hồ sơ claim cho Vận Hành Kinh Doanh phê duyệt và đẩy SAP*

Sau khi tạo đầy đủ các xe cần claim bù tồn và đính , lên Vận hành Kinh Doanh: Chọn Điều khiển = Send for Approve =&gt; Bấm Lưu/Save

Hồ sơ claim chuyển sang trạng thái Waiting HO

 Vận hành kinh , claim tự động đẩy sang SAP =&gt; Trạng thái hồ sơ claim chuyển sang Waiting SAP

 phê duyệt hồ sơ claim dưới SAP, trạng thái trên DMS chuyển sang SAP Approved

Lưu ý:

- Trường hợp kế toán reject dưới SAP, trạng thái hồ sơ claim trên DMS chuyển thành SAP Rejected, reopen lại hồ sơ claim và chỉnh sửa thông tin cần thiết sau đó gửi phê duyệt lại từ đầu.

- Người dùng kiểm tra lý do từ chối/Reject Reason của sơ claim

2. **Cấn trừ công nợ PO sơ claim**

1. * cấn trừ công nợ sơ claim*

- Chỉ thêm đơn mua hàng PO cần cấn trừ đối với Type/Loại = Offset Debt (Cấn trừ công nợ)
- Người dùng có thể tạo PO cấn trừ công nợ trước và hoặc sau khi hồ sơ claim đẩy sang SAP cho đến khi claim hết số tiền CTKM.

Người dùng vào mục Offset Debt Details, chọn :

Người dùng điền thông tin đơn hàng PO và số tiền cấn đơn hàng:

- Purchase Order: chọn PO đã sinh số (SO) tiền cấn

, hệ thống tạo thành công chi tiết thông tin đơn mua hàng cần cấn trừ công nợ.

**Lưu ý:**

- **Tổng tiền cấn PO không được lớn hơn tổng tiền khuyến mại NPP được claim**
- **NPP cấn trừ nhiêu đơn mua hàng PO thì tạo bấy nhiêu Offset Debt Details**

2. * tin PO cấn trừ sang SAP*

- Sau khi hồ sơ claim đã được dưới SAP, dùng bấm nút Submit Claim to SAP để đẩy thông tin các PO cấn trừ thêm bổ sung sang SAP.

 duyệt các PO này, hệ thống sẽ cập nhật chứng từ SAP FI và trạng thái

 reject, DMS sẽ cập nhật trạng thái về Rejected

Người dùng cần claim lại đơn hàng PO này thì tạo mới 1 Offser Debt detail mới để add PO. Hệ thống cấn PO đã bị reject vào tổng tiền cấn trừ.