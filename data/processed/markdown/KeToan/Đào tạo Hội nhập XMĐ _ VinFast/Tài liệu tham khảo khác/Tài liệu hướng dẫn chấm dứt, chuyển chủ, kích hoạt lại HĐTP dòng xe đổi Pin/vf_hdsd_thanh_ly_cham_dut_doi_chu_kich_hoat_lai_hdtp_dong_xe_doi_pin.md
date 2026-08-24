---
document_id: KETO704
title: VF HDSD Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin
source_file: VF_HDSD_Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin.docx
source_path: KeToan/VF_HDSD_Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe
  đổi Pin.docx
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
processed_at: '2026-08-20'
---

# VF HDSD Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin

# QUY TRÌNH THANH LÝ HĐTP XE MAX

Áp dụng cho trường hợp thanh lý HĐTP xe MAX thông thường. Với xe MAX sử dụng 02 PIN, người dùng có thể thực hiện 02 hoạt động tháo PIN trên cùng 01 Lệnh sửa chữa.

## Tạo Lệnh sửa chữa và thêm nội dung sửa chữa PIN

- Tạo mới Lệnh sửa chữa cho xe cần thanh lý HĐTP.

- Tại màn hình thêm nội dung sửa chữa, chọn Job Type = “09 - Sửa chữa PIN”.

- Chọn dịch vụ/mã công việc phù hợp để thực hiện kiểm tra tình trạng PIN.

- Nhập các thông tin bắt buộc khác theo quy trình hiện hành, sau đó chọn Save/Lưu.

Hình 2. Thêm nội dung sửa chữa PIN trên Lệnh sửa chữa

Cố vấn dịch vụ có thể thêm các dịch vụ và phụ tùng khác nếu xe cần sửa chữa/bảo dưỡng ngoài phạm vi sửa chữa PIN.

Sau đó, thực hiện quy trình báo giá và chuyển thành Work Order/Lệnh sửa chữa như quy trình đang chạy.

## Thêm hoạt động tháo PIN trên tab PIN Activity

- Mở Lệnh sửa chữa vừa tạo.

- Chọn tab “PIN Activity”.

- Chọn “Hoạt động sửa chữa mới” để tạo hoạt động tháo PIN.

Hình 3. Vào tab PIN Activity và thêm hoạt động sửa chữa

## Điền thông tin hoạt động “10. Tháo PIN kiểm tra tình trạng PIN”

Người dùng nhập thông tin cho hoạt động tháo PIN như sau:

- Dịch vụ: chọn “10. Tháo PIN kiểm tra tình trạng PIN”.

- Serial: mã serial PIN theo thông tin hệ thống/scan thực tế.

- Device Information: bản ghi thông tin PIN đang được hệ thống ghi nhận trên HĐTP theo số Vin.

- Actual Device Information: chọn PIN thực tế đang lắp trên xe tại thời điểm tháo PIN.

- Use Status / Actual Status Device Information: chọn trạng thái thực tế của PIN, ví dụ Good hoặc Broken.

- Thông tin lịch trình: nhập thời gian bắt đầu, thời gian kết thúc, khoảng thời gian.

Lưu ý: Actual Device Information là PIN thực tế đang lắp trên xe tại thời điểm thực hiện tháo PIN.

Trường hợp PIN thực tế đang lắp trên xe khác với PIN đang được ghi nhận trên HĐTP, người dùng cần chọn đúng PIN thực tế tại field Actual Device Information để hệ thống cập nhật lại thông tin PIN thực tế của xe trước khi thực hiện thanh lý HĐTP.

Hình 4. Điền thông tin hoạt động tháo PIN và Actual Device Information

## Lưu và hoàn thành hoạt động tháo PIN

- Sau khi nhập đủ thông tin, chọn Lưu.

- Kỹ thuật viên/đốc công thực hiện kiểm tra PIN theo thực tế.

- Chọn “Đánh dấu hoàn thành” sau khi hoạt động tháo PIN hoàn tất.

Hình 5. Đánh dấu hoàn thành hoạt động tháo PIN

## Thanh lý 02 PIN trên cùng 01 Lệnh sửa chữa

Đối với xe MAX sử dụng 02 PIN, thực hiện lặp lại bước thêm hoạt động PIN Activity để tạo đủ 02 hoạt động “10. Tháo PIN kiểm tra tình trạng PIN” trên cùng một Lệnh sửa chữa.

- Hoạt động thứ nhất: ghi nhận PIN thứ nhất thực tế đang lắp trên xe.

- Hoạt động thứ hai: ghi nhận PIN thứ hai thực tế đang lắp trên xe.

- Cả hai hoạt động phải được đánh dấu Hoàn thành trước khi tiếp tục đưa lệnh lên Quyết toán.

## Đóng lệnh sửa chữa và hoàn thành thanh toán

- Sau khi tất cả hoạt động tháo PIN đã hoàn thành, thực hiện các bước còn lại của Lệnh sửa chữa theo quy trình hiện hành.

- Thực hiện quyết toán, hoàn thành thanh toán lệnh, xuất hóa đơn/thu tiền nếu có phát sinh.

- Đảm bảo trạng thái Lệnh sửa chữa phải ở hoàn thành thanh toán trước khi thực hiện thanh lý trên EMSP.

Hình 6. Lệnh sửa chữa ở trạng thái Hoàn thành thanh toán

## Thực hiện thanh lý trên EMSP và cập nhật trạng thái trên DMS

- Đăng nhập hệ thống EMSP.

- Thực hiện chức năng thanh lý HĐTP theo quy trình EMSP.

- Để thao tác thanh lý được ở Emsp, cần thỏa mãn các yêu cầu dưới đây

- Hợp đồng pin đang ở trạng thái Active (đang hoạt động)

- Không có quả pin nào đang ở trạng thái Pending Active trong gói

- Không còn phiên sạc đang chạy

- Không còn nợ bill sạc chưa thanh toán

- Lệnh sửa chữa liên quan đã hoàn thành (kiểm tra qua DMS)

- Các bước thao tác trên Emsp:

- Truy cập Hệ thống EMSP > Xe máy > Quản lý hợp đồng khách hàng — XMĐ

- Tìm kiếm hợp đồng cần thanh lý: Nhập VinXe vào ô tìm kiếm và ấn enter. Xác nhận hợp đồng có trạng thái Active

- Nhấn icon Thanh lý: Nhấn biểu tượng thùng rác màu đỏ ở cột Thao Tác. Popup “Thanh lý hợp đồng Pin” xuất hiện

- Xác nhận thông tin hợp đồng: Kiểm tra mã SAP CustomerID, Vinxe, Ngày kích hoạt, Ngày hết hạn hiển thị đúng

- Nhấn KIỂM TRA CÔNG NỢ: Hệ thống kiểm tra nợ cước và phiên sạc

- Nếu bảng Thông tin thanh toán hiển thị “Không tìm thấy bản ghi nào” nghĩa là Khách hàng không còn nợ, Cơ sở thao tác tiếp

- Nếu Hệ thống hiển thị danh sách bill truy thu trong bảng Thông tin thanh toán, Cơ sở thông báo Khách hàng và tạo QR để Khách hàng thanh toán.

- Kiểm tra Danh sách hợp đồng pin: Xác nhận đúng mã hợp đồng pin, Serial pin, Mã hợp đồng pin cần thanh lý.

- Kiểm tra Mã Showroom & Tên Showroom: Hệ thống tự điền sẵn. Chỉnh sửa nếu cần thiết.

- Nhấn [THANH LÝ HỢP ĐỒNG]: Xác nhận thao tác. Hệ thống xử lý và hiển thị thông báo thanh lý thành công.

- Sau khi EMSP thanh lý thành công, hệ thống gửi kết quả về DMS.

- Trên DMS, HĐTP chuyển sang trạng thái “Waitting to terminate”.

## Hướng dẫn chuyển trạng thái Waiting to terminate sang terminated

Với luồng cũ, các cơ sở khi chấm dứt HĐ trên EMSP thì sẽ đồng bộ sang DMS. Hợp đồng trên DMS sẽ chuyển sang trạng thái “Terminate” và các cơ sở có thể tạo HĐ mới trên Đơn hàng bằng nút “Đổi chủ Hợp Đồng thuê pin”.

Tuy nhiên với luồng mới, khi HĐ trên EMSP chấm dứt, hợp đồng trên DMS sẽ chuyển sang trạng thái “Waiting to Terminate” nên sẽ nút đổi chủ sẽ chưa xuất hiện trên Đơn hàng.

Các cơ sở thao tác như sau để chấm dứt hoàn toàn HĐTP trên DMS và tạo HĐ mới (mục 6.2 trong tài liệu):

Bước 1: Tại màn hình Battery Rental ở trạng thái Waiting to terminate, người dùng chọn tab Contract/s và chọn nút Add new contract management

Hệ thống hiển thị màn hình tạo mới contract management

Bước 2: Tại màn hình tạo mới, người dùng chọn và nhập như sau:

- Type / Loại: Liquidation / Thanh lý

- Contract status / Trạng thái: Active / Kích hoạt

- Contract date / Ngày HĐ: Ngày ký

- Chọn nút SAVE

Bước 3: Người dùng chọn upload file, và tải lên file biên bản thanh lý đã được hoàn thành ký và chọn nút SAVE

Sau khi chọn SAVE, người dùng chọn nút Refresh trên ribon để load lại màn hình, link biên bản thanh lý sẽ được fill vào field File Url. Người dùng có thể xem lại biên bản thanh lý bằng cách chọn như ảnh để tải biên bản thanh lý đã upload về máy local.

File được upload thành công và ở trạng thái Active, bản ghi Battery Rental sẽ chuyển sang trạng thái Terminated. Hoàn tất thanh lý hợp đồng thuê pin.

Nút “Đổi chủ Hợp Đồng Thuê PIN” cũng sẽ được hiện trên đơn hàng.

Trường hợp  muốn up biên bản thanh lí mà khác BU, vì các cơ sở sẽ không thấy HĐTP của cơ sở khác:

Điều hướng dến Khu vực làm việc > Contract Management > + New.

Cơ sở điền các thông tin:

- Type: Liquidation.

- Contract Status: Active.

- Contract Date: Ngày kí biên bản thanh lí.

- Battery Rental Ref: mã HĐTP.

- VIN no: số VIN

Lưu ý: Số VIn và Mã HĐTP phải được điền đúng và khớp nhau, nếu không hệ thống sẽ báo lỗi.

Ấn Lưu để Lưu bản ghi. Sau đó, cơ sở ấn "Chọn tệp" để up giấy tờ:

## Các thông báo lỗi thường gặp & cách xử lý

| Thông báo lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Nút [Thanh lý] không hiển thị | HĐ chưa Active hoặc đã Thanh lý | Kiểm tra trạng thái HĐ. Chỉ thanh lý được HĐ đang Active. |
| "Chỉ thanh lý được hợp đồng đang Active" | HĐ ở trạng thái khác Active | Liên hệ bộ phận kỹ thuật nếu cần điều chỉnh. |
| Hệ thống chặn vì có quả PendingActive | 1 quả pin trong gói chưa được kích hoạt | Kích hoạt quả pin PendingActive trước, sau đó thực hiện thanh lý. |
| Còn phiên sạc đang chạy | KH đang có phiên sạc chưa tổng hợp | Chờ phiên sạc kết thúc và được tổng hợp lên bill rồi thử lại. |
| Còn nợ bill sạc chưa thanh toán | TypeBill 6 hoặc 16 chưa trả | Yêu cầu KH thanh toán nợ sạc trước khi thanh lý. |
| Chờ lệnh sửa chữa hoàn thành | DMS còn lệnh sửa chữa chưa đóng | Phối hợp với bộ phận kỹ thuật đóng lệnh sửa chữa rồi thử lại. |

9. Lưu ý quan trọng

| ❗ KHÔNG THỂ HOÀN TÁC: Sau khi nhấn [THANH LÝ HỢP ĐỒNG] và xác nhận thành công, thao tác không thể hoàn tác. Hãy kiểm tra kỹ thông tin trước khi xác nhận. |
| --- |

- Chỉ thực hiện thanh lý khi có yêu cầu chính thức từ khách hàng.

- Kiểm tra kỹ VinXe trước khi thực hiện để tránh nhầm hợp đồng.

- Mã Showroom và Tên Showroom phải chính xác — liên quan đến phân bổ doanh thu.

- Khi thanh lý 2 quả pin cùng lúc, đảm bảo cả 2 lệnh sửa chữa đều đã hoàn thành.

- Thông tin thanh lý sẽ được đồng bộ tự động sang DMS và SAP sau khi hoàn tất.

- Mọi thắc mắc hoặc lỗi ngoài danh sách ở mục 8, vui lòng liên hệ bộ phận IT Support.

# QUY TRÌNH CHUYỂN CHỦ HĐTP XE MAX

Áp dụng khi khách hàng có nhu cầu chuyển chủ xe và chuyển quyền sử dụng hợp đồng thuê Pin sang khách hàng mới.

## Tạo HĐ chuyển nhượng trên DMS

- Trên DMS, truy cập: Khu vực làm việc > Device Information > Battery Information Overview.

- Tìm kiếm theo số VIN của xe cần chuyển chủ.

- Mở bản ghi Device Information và chọn [Chuyển chủ HĐTP].

- Tại màn hình New Battery Rental, nhập đầy đủ thông tin:

- Lý do tạo hợp đồng: nhập nội dung phù hợp, ví dụ “Hợp đồng chuyển chủ”.

- Lựa chọn loại gói cước: Old package hoặc New package.

- Chọn khách hàng mới nhận chuyển chủ.

- Chọn tab Thông tin thanh toán (Payment Info). ​Chọn loại giao dịch là Refund deposit hoặc Transfer Deposit tùy theo mong muốn của khách hàng là Chuyển cọc hay Hoàn cọc sau đó chọn Save để tạo HĐTP của chủ mới

Lưu ý: Đối với xe có 02 Hợp đồng thuê Pin, sau khi Hợp đồng Pin thứ nhất được tạo thành công, hệ thống sẽ tự động tạo Hợp đồng Pin thứ hai.

Người dùng cần thực hiện đính kèm tài liệu trên từng Hợp đồng Pin (bao gồm cả hợp đồng được hệ thống tự động tạo) để đảm bảo mỗi hợp đồng đều có đầy đủ hồ sơ đính kèm.

Tài liệu bao gồm:

- PL Văn bản tiếp nhận HĐTP XMĐ, Ô tô điện (Đổi chủ xe) T3.2026

- Giấy tờ mua bán có công chứng hoặc photo đăng ký xe đứng tên chủ mới

- HĐTP ký kết giữa chủ mới và ĐLPP

- CCCD hoặc ĐKKD & GUQ của chủ mới (GUQ trong trường hợp người ký ở bản cứng HĐTP không phải chính chủ HĐTP trên hệ thống

## Thực hiện chuyển chủ hợp đồng thuê Pin trên EMSP

- Đăng nhập EMSP và thực hiện thanh lý hợp đồng của chủ cũ với Type = Đổi chủ.

- Hệ thống kiểm tra các điều kiện sau:

- Kiểm tra công nợ Bill thuê Pin, sạc Pin

- Kiểm tra hợp đồng đổi chủ tạo trên DMS (trạng thái Open) và đã Attachment file Scan Hợp đồng, giấy tờ theo yêu cầu quy định

- Nếu không thỏa mãn điều kiện thông báo lỗi trên EMSP không cho phép Đổi chủ hợp đồng thuê PIN

- Nếu thỏa màn cho phép thanh lý hợp đồng của khách hành cũ và Kích hoạt hợp đồng của khách hành mới

- Hướng dẫn chuyển chủ trên Emsp như sau:

### Trường hợp 1: Không có nợ cước (0 VND)

Áp dụng khi khách hàng không có nợ cước thuê pin, không có phiên sạc đang chạy và DMS đã tạo hợp đồng ảo hợp lệ cho chủ mới.

Ảnh 1 :

Ảnh 2:

| 1 | Mở màn hình Quản lý hợp đồng khách hàng — XMĐ Vào EMSP > Xe máy > Quản lý hợp đồng khách hàng — XMĐ. |
| --- | --- |
| 2 | Tìm kiếm hợp đồng cần thanh lý chuyển chủ Nhập VinXe vào ô tìm kiếm. Xác nhận hợp đồng của chủ cũ đang ở trạng thái Active. |
| 3 | Nhấn icon Thanh lý chuyển chủ Chọn thao tác thanh lý tại hợp đồng cần xử lý. Popup xác nhận thông tin hợp đồng xuất hiện. |
| 4 | Xác nhận thông tin hợp đồng Kiểm tra SapCustomerId, VinXe, ContractNo, ngày kích hoạt và ngày hết hạn. |
| 5 | Nhấn [KIỂM TRA CÔNG NỢ] Hệ thống kiểm tra công nợ thuê pin, phiên sạc đang chạy và bill sạc chưa thanh toán. |
| 6 | Kiểm tra kết quả công nợ Tổng tiền cần thanh toán là 0 VND và không còn điều kiện chặn từ ChargingService. Note:  Nếu khách hàng không có bill nợ thuê pin trả trước => Hệ thống không tạo bill truy thu.  Nếu có nợ thuê pin trả trước. Hệ thống tự động tạo bill thuê pin để truy thu tiền của khách hàng. |
| 7 | EMSP kiểm tra hợp đồng ảo trên DMS Nhân viên chọn [Thanh lý chuyển chủ ]  Hệ thống gọi DMS để xác nhận đã tồn tại hợp đồng ảo hợp lệ cho chủ mới. |
| 8 | Xác nhận kết quả kiểm tra DMS Chỉ tiếp tục khi DMS trả về đã có hợp đồng ảo; nếu chưa có hoặc lỗi kết nối, hệ thống phải chặn thao tác. |
| 9 | Kiểm tra danh sách pin và thông tin Showroom Xác nhận đúng hợp đồng pin, Serial pin, mã Showroom và tên Showroom. |
| 10 | Nhấn [THANH LÝ CHUYỂN CHỦ] Xác nhận thao tác. Hệ thống xử lý và hiển thị thông báo hoàn tất thành công. |

| ✅ Kết quả: Hợp đồng của chủ cũ chuyển sang trạng thái Thanh lý chuyển chủ (Status = 3). Ngày thanh lý được ghi nhận; kết quả được đồng bộ sang DMS để tiếp tục xử lý hợp đồng của chủ mới. |
| --- |

### Trường hợp 2: Có nợ cước thuê pin

Áp dụng khi khách hàng còn nợ cước thuê pin. Khách hàng phải hoàn tất thanh toán; sau đó EMSP tiếp tục kiểm tra hợp đồng ảo của chủ mới trên DMS trước khi cho phép thanh lý chuyển chủ.

Ví dụ: Hợp đồng hết hạn ngày 30/06/2026, khách hàng thanh lý chuyển chủ ngày 15/07/2026. EMSP tạo Bill truy thu cho 01 hoặc 02 pin theo trọn kỳ từ 01/07/2026 đến 31/07/2026; khách hàng phải thanh toán trước khi hoàn tất thanh lý.

| 1 | Thực hiện các bước 1–5 như Trường hợp 1 Mở màn hình, tìm hợp đồng, kiểm tra thông tin và nhấn [KIỂM TRA CÔNG NỢ]. |
| --- | --- |
| 2 | Kiểm tra bill truy thu Hệ thống hiển thị các bill còn nợ và tổng số tiền khách hàng cần thanh toán. |
| 3 | Khách hàng thực hiện thanh toán Khách hàng thanh toán toàn bộ công nợ qua kênh được chỉ định. |
| 4 | Hệ thống xác nhận thanh toán Sau khi nhận callback thành công, hệ thống cập nhật trạng thái các bill và cho phép tiếp tục. |
| 5 | EMSP gọi DMS kiểm tra hợp đồng ảo Chỉ khi DMS xác nhận đã có hợp đồng ảo hợp lệ cho chủ mới, hệ thống mới mở thao tác thanh lý chuyển chủ. |
| 6 | Nhấn [THANH LÝ CHUYỂN CHỦ] Hoàn tất quy trình. Hợp đồng của chủ cũ chuyển sang trạng thái Thanh lý chuyển chủ. |

| ⚠ Lưu ý tính tiền truy thu: Số tiền truy thu được tính theo số tháng nợ. Ví dụ: 3 tháng nợ x 175.000 VND = 525.000 VND. Tháng lẻ tính theo số ngày thực tế. |
| --- |

### Các trường hợp đặc biệt

- Gói thuê có 2 quả pin

| 📌 Quy tắc: Khi gói có 2 quả pin, hệ thống xử lý 2 quả cùng lúc. Việc thanh lý chuyển chủ chỉ được thực hiện khi hợp đồng ảo trên DMS bao phủ đúng các quả pin cần chuyển giao. |
| --- |

- Thanh lý 2 quả cùng lúc:

- Hệ thống kiểm tra hợp đồng ảo trên DMS cho từng quả pin cần chuyển giao.

- Cả 2 quả được thanh lý chuyển chủ đồng thời nếu đều được ghi nhận hợp lệ trong hợp đồng ảo của chủ mới.

- Hợp đồng KH chuyển sang trạng thái Thanh lý chuyển chủ (Status = 3), BatteryContracts = [].

- DMS nhận kết quả thanh lý chuyển chủ thành công cho các quả pin tương ứng.

- Kiểm tra hợp đồng ảo trên DMS

Trước khi cho phép chấm dứt hợp đồng của chủ cũ, EMSP tự động gọi sang DMS để kiểm tra hợp đồng ảo đã được tạo cho chủ mới.

- Nếu DMS chưa có hợp đồng ảo, hợp đồng ảo chưa hợp lệ hoặc DMS không phản hồi: Hệ thống chặn thanh lý chuyển chủ và hiển thị thông báo yêu cầu hoàn tất hợp đồng ảo trên DMS.

- Nếu DMS xác nhận đã có hợp đồng ảo hợp lệ: Hệ thống cho phép nhân viên tiếp tục và hoàn tất luồng thanh lý chuyển chủ.

| ⚠ Lưu ý: Nhân viên cần phối hợp với bộ phận DMS để hoàn tất hợp đồng ảo cho chủ mới trước khi thực hiện thanh lý chuyển chủ. |
| --- |

- Phiên sạc đang chạy hoặc nợ bill sạc

| Phiên sạc đang chạy | Hệ thống ChargingService phát hiện phiên chưa tổng hợp → Chặn thanh lý. Chờ phiên sạc kết thúc. |
| --- | --- |
| Nợ bill sạc (TypeBill 6/16) | Hệ thống phát hiện nợ sạc chưa thanh toán → Chặn thanh lý. KH cần thanh toán bill sạc trước. |
| Không còn phiên, không nợ sạc và đã có hợp đồng ảo | Hệ thống cho phép tiếp tục luồng thanh lý chuyển chủ. |

Các lỗi liên quan đến sạc, ĐLPP gửi email cho

- Kích hoạt hợp đồng cho chủ mới sau thanh lý chuyển chủ

Áp dụng sau khi hợp đồng của chủ cũ đã chuyển sang trạng thái Thanh lý chuyển chủ và DMS tiếp tục đồng bộ hợp đồng của chủ mới sang EMSP.

- DMS đồng bộ hợp đồng của chủ mới sang EMSP trên cơ sở hợp đồng ảo đã được xác nhận trước đó.

- NV thực hiện thanh toán trên EMSP Portal, chọn số tháng muốn thanh toán.

- Hệ thống gen bill đúng số tiền theo số tháng và loại pin (quả 1: 175.000/tháng, quả 2: 125.000/tháng).

- Hệ thống cho phép Active hợp đồng với chủ mới.

| 💡 Gợi ý: Nếu Active 2 quả không đồng thời, hệ thống tự căn chỉnh số tháng của quả thứ 2 để khớp dueDate với quả thứ 1. |
| --- |

​Lưu ý:

- HĐTP của chủ cũ chỉ chuyển trạng thái Terminated / Đã thanh lý khi tiền cọc thuê pin ở DMS và SAP cùng giá trị. Lúc này thông tin Transfer Or Refund trên HĐTP của chủ cũ có giá trị là Yes

- Trường hợp giá trị cọc pin ở DMS và SAP không khớp, HĐTP của chủ cũ ở trạng thái Waiting to terminate và thông tin Transfer Or refund trên HĐTP của chủ cũ có giá trị là No

- Trường hợp giá trị cọc pin không khớp, cơ sở cần kiểm tra lại thông tin sau đó chọn Transfer Or Refund = Yes và chọn Save để chuyển trạng thái HĐTP của chủ cũ là Terminated / Đã thanh lý

## Hướng dẫn chuyển cọc khi chuyển chủ HĐTP

​Sau khi HĐTP của chủ cũ ở trạng thái Terminated / Đã thanh lý, hệ thống sẽ tự động tạo Yêu cầu phê duyệt ở trạng thái Open / Mở. Yêu cầu được tạo mới là yêu cầu Hoàn cọc hay Chuyển cọc phụ thuộc vào lựa chọn của cơ sở trên màn hình HĐTP của chủ mới tại Bước 2

- Người dùng đính kèm file và phát hành DPR gửi QLV phê duyệt.

- Sau khi DPR được phê duyệt, HĐTP tương ứng được chuyển sang trạng thái Active/Đang hoạt động.

## Các thông báo lỗi thường gặp & cách xử lý

| Thông báo lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| Nút [Thanh lý] không hiển thị | Hợp đồng chưa Active hoặc đã Thanh lý chuyển chủ | Kiểm tra trạng thái hợp đồng. Chỉ hợp đồng Active mới được thực hiện thanh lý chuyển chủ. |
| “Chỉ thanh lý chuyển chủ được hợp đồng đang Active” | HĐ ở trạng thái khác Active | Liên hệ bộ phận kỹ thuật nếu cần điều chỉnh. |
| Hệ thống chặn vì có quả PendingActive | 1 quả pin trong gói chưa được kích hoạt | Kích hoạt quả pin PendingActive trước, sau đó thực hiện thanh lý. |
| Còn phiên sạc đang chạy | KH đang có phiên sạc chưa tổng hợp | Chờ phiên sạc kết thúc và được tổng hợp lên bill rồi thử lại. |
| Còn nợ bill sạc chưa thanh toán | TypeBill 6 hoặc 16 chưa trả | Yêu cầu khách hàng thanh toán nợ sạc trước khi thanh lý chuyển chủ. |
| Chưa có hợp đồng ảo của chủ mới | DMS chưa tạo hợp đồng ảo, hợp đồng ảo chưa hợp lệ hoặc DMS không phản hồi | Hoàn tất việc tạo hợp đồng ảo trên DMS và thực hiện kiểm tra lại trước khi thanh lý chuyển chủ. |

## Lưu ý quan trọng

| ❗ KHÔNG THỂ HOÀN TÁC: Sau khi nhấn [THANH LÝ CHUYỂN CHỦ] và xác nhận thành công, hợp đồng của chủ cũ sẽ chuyển sang trạng thái Thanh lý chuyển chủ. Hãy kiểm tra kỹ VIN, chủ mới và kết quả xác nhận hợp đồng ảo trên DMS trước khi thực hiện. |
| --- |

- Chỉ thực hiện thanh lý chuyển chủ khi có yêu cầu chính thức và thông tin chủ mới đã được xác nhận trên DMS.

- Kiểm tra kỹ VinXe trước khi thực hiện để tránh nhầm hợp đồng.

- Mã Showroom và Tên Showroom phải chính xác — liên quan đến phân bổ doanh thu.

- Khi thanh lý 2 quả pin cùng lúc, đảm bảo hợp đồng ảo của chủ mới trên DMS đã bao phủ đầy đủ các quả pin cần chuyển giao.

- Sau khi hoàn tất, hợp đồng của chủ cũ được cập nhật sang trạng thái Thanh lý chuyển chủ; kết quả được đồng bộ sang DMS và SAP theo luồng hệ thống.

- Mọi thắc mắc hoặc lỗi ngoài danh sách ở mục 6, vui lòng liên hệ bộ phận IT Support.

# QUY TRÌNH KÍCH HOẠT HĐTP CỦA PIN 2

Bước 1. Tạo lệnh sửa chữa và thực hiện hoạt động lắp Pin 2 cho thuê

- WO ở trạng thái lệnh sửa chữa/released -> tab Pin activity -> New WO service activity -> Tạo hoạt động Pin 14 (Pin đã kích hoạt tài sản và ở trạng thái unlease/at BU)

- Sau khi điền đủ thông tin bấm Save để lưu hoạt động -> Bấm Mark complete để hoàn thành hoạt động Pin

- Chuyển WO sang trạng thái Invoiced.

Bước 2. Tạo và kích hoạt HĐTP cho Pin 2 (Pin thuê)

- Mở bản ghi device information theo serial Pin đã thực hiện xong hoạt động 14 -> Bấm “HĐ Pin 2”

- Điền thông tin Lựa chọn loại gói cước, Khách hàng, Battery Option trên form HĐ mới -> Save

- Thêm Package Type, đính kèm hồ sơ và phát hành phiếu thu cọc (nếu có).

- Kích hoạt gói cước

# KÍCH HOẠT LẠI HĐTP CHO VINXE ĐÃ THỰC HIỆN THANH LÝ PIN VỀ VINFAST

Để thực hiện Kích hoạt lại hợp đồng thuê PIN, người dùng thao tác như sau:

Đầu tiên cần tạo Lệnh sửa chữa (LSC) để lắp PIN lên xe để thực hiện cho thuê

Bước 1: Lệnh sửa chữa (LSC) để kiểm tra PIN

Cố vấn dịch vụ chọn tạo mới, tiến hành thêm thông tin sửa chữa yêu cầu bởi hệ thống(các trường bắt buộc), thông tin về xe, khách hàng và phương tiện, sau đó chọn Lưu

Bước 1.1: Thêm Nội dung sửa chữa Tháo lắp PIN

Cố vấn dịch vụ tiến hành thêm Nội dung sửa chữa để thay thế PIN đã bán cho khách

Giao diện danh sách Nội dung và phụ tùng hiển thị

Đối với nội dung sửa chữa, chọn loại “09- Sửa chữa PIN”. Chọn mã công việc lắp pin cho thuê

Cố vấn dịch vụ có thể thêm các dịch vụ và phụ tùng khác nếu xe cần sửa chữa/bảo dưỡng ngoài phạm vi thay PIN cho thuê.

Sau đó, thực hiện quy trình báo giá và chuyển thành Work Order/Lệnh sửa chữa như quy trình đang chạy.

Bước 1.2: Thêm Hoạt động sửa chữa, Tháo PIN và Lắp PIN kiểm tra

- Thêm hoạt động “12. Lắp PIN cho thuê trước khi kích hoạt HĐ”

CVDV thêm hoạt động sửa chữa tháo PIN của khách. Vào mục Pin Activity --> Hoạt động dịch vụ mới

Màn hình thêm hoạt động sửa chữa hiện lên, nhập các thông tin

- Dịch vụ: Chọn  “12. Lắp PIN cho thuê trước khi kích hoạt HĐ”

- Serial PIN: Tự động fill serial PIN khách đang thuê vào, KTV có thể scan lại mã PIN

- Use status: Nhập trạng thái sử dụng của viên PIN. Tốt (good) hoặc Hỏng (broken)

- Kĩ thuật viên: Chọn KTV để giao việc

- Khoang sửa chữa: Khoang sửa chữa

- Thông tin lịch trình: Chọn thông tin lịch trình sửa chữa

- Lưu ý: cho phép gắn các Pin tài sản đang không cho thuê hoặc PIN mới dành cho mục đích cho thuê

Sau khi hoàn thành, nhấn chọn Lưu.

Kĩ thuật viên thực hiện tháo PIN, đốc công sẽ đóng hoạt động sau khi PIN được tháo thành công

- Thêm hoạt động sửa chữa “13. Tháo PIN khỏi xe trước khi kích hoạt HĐ”  (chỉ thực hiện nếu không có nhu cầu gắn PIN để kích hoạt hợp đầu nữa hoặc muốn lắp PIN khác)

CVDV thêm hoạt động sửa chữa Lắp PIN mới cho khách. Vào mục PIN Activity --> Hoạt động dịch vụ mới

Màn hình thêm hoạt động sửa chữa hiện lên, nhập các thông tin

- Dịch vụ: Chọn 13. Tháo PIN khỏi xe trước khi kích hoạt HĐ

- Serial : Kĩ thuật viên Scan serial PIN

- Use status: Nhập trạng thái sử dụng của viên PIN. Tốt (good) hoặc Hỏng (broken)

- Kĩ thuật viên: Chọn KTV để giao việc

- Khoang sửa chữa: Khoang sửa chữa

- Thông tin lịch trình: Chọn thông tin lịch trình sửa chữa

Sau khi hoàn thành, nhấn chọn Lưu.

Kĩ thuật viên thực hiện lắp PIN, CVDV sẽ đóng phiếu sau khi PIN được lắp thành công

c) Dừng kích hoạt các hoạt động Pin Activity

Chọn Dừng kích hoạt từng hoạt động Pin Activity

Theo thứ tự:

12. Lắp PIN cho thuê trước khi kích hoạt HĐ

13. Tháo PIN khỏi xe trước khi kích hoạt HĐ (nếu có)

Bước 2: Đóng lệnh sửa chữa

Sau khi Tất cả các Hoạt động sửa chữa đã được đóng, thực hiện quy trình còn lại giống như quy trình đã chạy, bao gồm:

- Quyết toán

- Xuất hóa đơn và thu tiền

- Quy trình Claim bảo hành (đối với dịch vụ được bảo hành)

Bước 3: Tạo HĐ Thuê PIN lại

Vào phần mềm DMS chọn Phân hệ Khu vực làm việc > Device Information > Battery Informaition Overview sS

- Tìm kiếm VIN xe cần Kích hoạt lại hợp đồng thuê PIN

- Tại màn hình chi tiết Device information > Nhấn [Thuê lại HD]

- Tại màn hình Battery Rental Mới

- Chọn Contract Tpye (nếu trường hợp VIN xe được chính sách nhiều gói cước)

- Sau đó chọn [Lưu]

- Tiếp tục chọn tab [Attachment file] để đính kèm các file Scan Hợp đồng, giấy tờ theo yêu cầu quy định

- Ở bước này, nếu KH thuê Pin không phải chủ HĐTP ban đầu, ĐLPP điền mã KH của chủ mới ở mục Khách hàng

Bước 4: Thực hiện Kích hoạt hợp đồng thuê PIN