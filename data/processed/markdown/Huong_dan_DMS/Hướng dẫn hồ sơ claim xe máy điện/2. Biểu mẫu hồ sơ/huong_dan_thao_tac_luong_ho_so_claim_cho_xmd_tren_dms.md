---
document_id: HUON120
title: Hướng dẫn thao tác luồng hồ sơ claim cho XMĐ trên DMS
source_file: Hướng dẫn thao tác luồng hồ sơ claim cho XMĐ trên DMS.pdf
source_path: Huong_dan_DMS/Hướng dẫn thao tác luồng hồ sơ claim cho XMĐ trên DMS.pdf
document_type: pdf
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
pages: 19
pii_processed: true
pii_removed: true
processed_at: '2026-08-22'
---

# Hướng dẫn thao tác luồng hồ sơ claim cho XMĐ trên DMS

## Page 1

Hồ sơ claim cho XMĐ Luồng claim tiền chênh lệch sỉ cho xe trước bán (Tồn kho) Tạo mới chi tiết hồ sơ claim cho xe tồn kho Đính kèm tài liệu trên hồ sơ claim Đính kèm tài liệu trên hồ sơ claim Đẩy thông tin PO cấn trừ sang SAP

## Page 2

1. Luồng claim tiền chênh lệch sỉ cho xe trước bán (Tồn kho)
a. Tạo mới tổng quan hồ sơ claim xe tồn kho
Áp dụng cho các trường hợp xe vẫn còn tồn kho, có thay đổi chính sách giá bán lẻ đối với xe đó
và kế toán đã phê duyệt giá bù tồn cho những xe này.
Người dùng chọn vào mục Kế toán/Cashier => Chọn Dealer Claim Payment => Bấm New/Tạo
mới
Sau khi bấm tạo mới, màn hình hiển thị giao diện hồ sơ claim, người dùng chọn và kiểm tra các
thông tin sau:
Bussiness Unit: Mã chi nhánh
Transaction Date/Ngày giao dịch
Type/Loại: Offset Debt/Cấn trừ công nợ
Claim Source: Inventory New Vehicle (Xe tồn kho)
Ngành hàng/VF Division: Xe máy điện/ Escooter

## Page 3

Sau khi lưu, hệ thống sinh ra bản ghi tổng quan hồ sơ claim cho NPP

b. Tạo mới chi tiết hồ sơ claim cho xe tồn kho
Người dùng chọn tab Claim Details (Chi tiết hồ sơ claim) => Bấm tạo mới Dealer Claim
Payment Details sau đó điền thông tin số tồn kho xe cần claim chênh lệch sỉ vào chi tiết.

## Page 4

Người dùng nhập số khung xe vào Invetory New Vehicle => Bấm lưu/Save=> Hệ thống tự động
lấy ra khoản tiền chênh lệch sỉ đã được kế toán phê duyệt.
Người dùng muốn claim tiền bù tồn cho bao nhiêu xe thì tạo bấy nhiêu chi tiết tương ứng cho hồ
sơ claim
Sau khi tạo chi tiết thành công, hệ thống tự động cộng tổng số tiền bù tồn cơ sở được claim ra
tổng quan hồ sơ claim.

## Page 5

1. Người dùng chỉ claim chênh lệch sỉ cho xe trước bán được khi bộ phận vận hành kinh
doanh đã tính toán xong tiền hồ sơ claim, đẩy lên hệ thống DMS và kế toán đã phê duyệt
bảng giá này.
2. Luồng claim bù tồn cho xe tồn kho chỉ áp dụng cho những số khung đang ở trạng thái
Tồn kho (Stock) - Có sẵn (Available)
3. Mỗi khoản bù tồn cho xe trước bán trong cùng 1 khoảng thời gian chỉ được claim trên 1
hồ sơ claim.
Người dùng tra cứu giá chênh lệch sỉ (bù tồn) cho từng số khung xe tại bảng Cashier/Kế toán =>
Chọn bảng Wholesale Priced Difference Config. Chỉ những bảng giá nào đã được kế toán phê
duyệt thì mới claim chênh lệch sỉ cho xe trước bán thành công.

## Page 6

c. Đính kèm tài liệu trên hồ sơ claim
Người dùng chọn mục Attachment File để đính kèm hồ sơ giấy tờ để phía VHKD phê duyệt
Sau khi chọn file và lưu => Đính kèm hồ sơ thành công

d. Gửi phê duyệt hồ sơ claim và đẩy sang SAP
Sau khi tạo đầy đủ các xe cần claim bù tồn và đính kèm tài liệu thành công, người dùng gửi phê
duyệt lên Vận hành Kinh Doanh: Chọn Điều khiển = Send for Approve => Bấm Lưu/Save

## Page 7

Hồ sơ claim chuyển sang trạng thái Waiting HO
Sau khi Vận hành kinh doanh phê duyệt thành công, hồ sơ claim tự động đẩy sang SAP =>
Trạng thái hồ sơ claim chuyển sang Waiting SAP

## Page 8

Sau khi kế toán phê duyệt hồ sơ claim dưới SAP, trạng thái trên DMS chuyển sang SAP
Approved
Trường hợp kế toán reject dưới SAP, trạng thái hồ sơ claim trên DMS chuyển thành SAP
Rejected, người dùng có thể reopen lại hồ sơ claim và chỉnh sửa thông tin cần thiết sau đó
gửi phê duyệt lại từ đầu.
Người dùng kiểm tra lý do từ chối/Reject Reason của kế toán trên hồ sơ claim

## Page 9

2. Luồng claim tiền CTKM cho xe đã xuất hóa đơn cho khách hàng cuối
Áp dụng cho các xe có các CTKM trừ thẳng vào giá xuất hóa đơn (fix discount, job level
discount, vinclub discount); quy đổi tiền mặt qua phiếu thu 51 hoặc bù tồn (khi chưa được claim
xe trước bán)
a. Tạo mới tổng quan hồ sơ claim cho đơn hàng NVSO
Người dùng chọn vào mục Kế toán/Cashier => Chọn Dealer Claim Payment => Bấm New/Tạo
mới

Sau khi bấm tạo mới, màn hình hiển thị giao diện hồ sơ claim, người dùng chọn và kiểm tra các
thông tin sau:

## Page 10

Bussiness Unit: Mã chi nhánh
Transaction Date/Ngày giao dịch
Type/Loại: Offset Debt/Cấn trừ công nợ
Claim Source: NVSO (Đơn hàng bán xe)
Ngành hàng/VF Division: Xe máy điện/ Escooter

b. Tạo mới chi tiết hồ sơ claim cho đơn hàng bán xe
Người dùng chọn tab Claim Details (Chi tiết hồ sơ claim) => Bấm tạo mới Dealer Claim
Payment Details sau đó điền thông tin đơn hàng bán xe (NVSO) cần claim vào chi tiết.

Người dùng nhập số đơn hàng bán xe (NVSO) vào NV Sale Order => Bấm lưu/Save

## Page 11

Sau khi lưu, hệ thống tự động tính ra số tiền NPP được claim cho từng đơn hàng (nếu có) bao
gồm tiền CTKM gốc và được claim sau khi đã tính theo chiết khấu NPP được hưởng:
Tiền giảm giá CTKM (Fix discount)
Tiền giảm giá cấp bậc CBNV (Job level discount)
Tiền giảm giá Vinclub
Quy đổi tiền mặt claim (Thu theo phiếu thu 51)
Tiền voucher (redeem voucher qua phiếu thu 34)
Tiền chênh lệch sỉ/bù tồn (Trường hợp xe chưa claim chênh lệch sỉ/bù tồn trước bán thì
sẽ tự động lấy khoản tiền này khi claim theo NVSO)
Sau đó hệ thống sẽ tự động tính ra tổng như sau:
Tiền KM trừ thẳng giá bán = Tiền giảm giá CTKM Claim + Tiền giảm giá CBNV
Claim + Tiền giảm giá Vinclub Claim
Quy đổi tiền mặt NVSO = Quy đổi tiền mặt claim + Tiền voucher claim
Tổng tiền KM đơn hàng = Tiền KM trừ thẳng giá bán + Quy đổi tiền mặt NVSO +
Tiền chênh lệch sỉ NVSO

## Page 12

NPP claim bao nhiêu đơn hàng thì tạo bấy nhiêu chi tiết cho hồ sơ claim.
Hệ thống tự động tính tổng tiền NPP claim ở ngoài giao dịch claim tổng (Bao gồm tiền gốc và
tiền NPP được claim)

## Page 13

Mỗi đơn hàng chỉ được claim hồ sơ 1 lần, trạng thái phải là Invoice/Hóa đơn
Mỗi xe chỉ được claim chênh lệch sỉ 1 lần trong cùng 1 khoảng thời gian, nếu đã claim xe
tồn kho rồi thì khi claim theo NVSO sẽ không có tiền chênh lệch sỉ
Số tiền NPP được claim cuối là giá ở cột Claim amount.

c. Đính kèm tài liệu trên hồ sơ claim
Người dùng chọn mục Attachment File để đính kèm hồ sơ giấy tờ để phía VHKD phê duyệt

## Page 14

Sau khi chọn file và lưu => Đính kèm hồ sơ thành công

d. Gửi hồ sơ claim cho Vận Hành Kinh Doanh phê duyệt và đẩy SAP
Sau khi tạo đầy đủ các xe cần claim bù tồn và đính kèm tài liệu thành công, người dùng gửi phê
duyệt lên Vận hành Kinh Doanh: Chọn Điều khiển = Send for Approve => Bấm Lưu/Save

## Page 15

Hồ sơ claim chuyển sang trạng thái Waiting HO
Sau khi Vận hành kinh doanh phê duyệt thành công, hồ sơ claim tự động đẩy sang SAP =>
Trạng thái hồ sơ claim chuyển sang Waiting SAP

## Page 16

Sau khi kế toán phê duyệt hồ sơ claim dưới SAP, trạng thái trên DMS chuyển sang SAP
Approved
Trường hợp kế toán reject dưới SAP, trạng thái hồ sơ claim trên DMS chuyển thành SAP
Rejected, người dùng có thể reopen lại hồ sơ claim và chỉnh sửa thông tin cần thiết sau đó
gửi phê duyệt lại từ đầu.
Người dùng kiểm tra lý do từ chối/Reject Reason của kế toán trên hồ sơ claim

## Page 17

3. Cấn trừ công nợ PO trên hồ sơ claim
a. Tạo mới chi tiết đơn hàng PO cần cấn trừ công nợ trên hồ sơ claim
− Chỉ thêm thông tin đơn mua hàng PO cần cấn trừ đối với Type/Loại = Offset Debt (Cấn
trừ công nợ)
− Người dùng có thể tạo PO cấn trừ công nợ trước và hoặc sau khi hồ sơ claim đẩy sang
SAP cho đến khi claim hết số tiền CTKM.
Người dùng vào mục Offset Debt Details, chọn tạo mới:
Người dùng điền thông tin đơn hàng PO và số tiền cấn trừ cho đơn hàng:
Purchase Order: Chỉ được chọn PO  đã sinh số đơn hàng SAP (SO) thành công

## Page 18

Số tiền cấn trừ trên PO

Sau khi lưu, hệ thống tạo thành công chi tiết thông tin đơn mua hàng cần cấn trừ công nợ.
Tổng tiền cấn trừ cho PO không được lớn hơn tổng tiền khuyến mại NPP được
claim
NPP cấn trừ cho bao nhiêu đơn mua hàng PO thì tạo bấy nhiêu Offset Debt Details

b. Đẩy thông tin PO cấn trừ sang SAP

## Page 19

Sau khi hồ sơ claim đã được kế toán phê duyệt dưới SAP, Người dùng bấm nút Submit
Claim to SAP để đẩy thông tin các PO cấn trừ thêm bổ sung sang SAP.

Sau Khi kế toán duyệt các PO này, hệ thống sẽ cập nhật chứng từ SAP FI và trạng thái chi tiết
sang Approved
Trường hợp bị reject, DMS sẽ cập nhật trạng thái về Rejected
Người dùng cần claim lại đơn hàng PO này thì tạo mới 1 Offser Debt detail mới để add PO. Hệ
thống sẽ tự động không tính số tiền cấn trừ trên PO đã bị reject vào tổng tiền cấn trừ.
Kết thúc luồng!