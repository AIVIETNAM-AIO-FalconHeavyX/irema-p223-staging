---
document_id: KETO558
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
processed_at: '2026-08-10'
---

# VF HDSD Thanh lý chấm dứt, đổi chủ, kích hoạt lại HĐTP dòng xe đổi Pin

########### Mục lục

QUY TRÌNH THANH LÝ HĐTP XE MAX	2

1.	Tạo Lệnh sửa chữa dung sửa chữa PIN	2

2.	Thêm hoạt động tháo PIN trên tab PIN Activity	2

3.	Điền thông tin hoạt động “10. Tháo PIN kiểm tra tình trạng PIN”	3

4.	Lưu và hoàn động tháo PIN	4

5. 01 Lệnh sửa chữa	4

6.	Đóng lệnh sửa chữa và hoàn toán	5

7.	Thực hiện thanh EMSP và cập nhật trạng thái 5

8.	Hướng dẫn chuyển trạng thái Waiting to terminate sang terminated	6

9. thường gặp &amp;

QUY TRÌNH CHUYỂN CHỦ HĐTP XE MAX	12

1. tin khách hàng mới trên DMS (Đã có khách hàng chuyển sang bước 2)	12

2.	Tạo HĐ chuyển nhượng 	12

3.	Thực hiện chuyển thuê Pin trên EMSP	14

Trường hợp 1: Không có nợ cước (0 VND)	15

Trường hợp 2: nợ cước thuê pin	17

Các trường hợp đặc biệt	19

4.	Hướng dẫn chuyển cọc 20

5. thường gặp &amp; 21

6. trọng	22

QUY TRÌNH KÍCH HOẠT HĐTP CỦA PIN 2	23

KÍCH HOẠT LẠI HĐTP CHO VINXE ĐÃ THỰC HIỆN THANH LÝ PIN VỀ VINFAST	27

#

## QUY TRÌNH THANH LÝ HĐTP XE MAX

Áp dụng cho xe thường. Với xe , hiện 02 hoạt động tháo PIN trên cùng 01 Lệnh sửa chữa.

### 1 Tạo Lệnh sửa chữa dung sửa chữa PIN

- Tạo mới Lệnh sửa chữa cho xe cần thanh lý HĐTP.
- Tại màn hình thêm nội dung sửa chữa, chọn Job Type = “09 - Sửa chữa PIN”.
- Chọn dịch vụ/mã công việc phù hợp để thực .
- tin bắt buộc khác theo quy , .

*Hình 2. nội dung sửa chữa PIN trên Lệnh sửa chữa*

Cố vấn dịch vụ có thể thêm các dịch vụ và phụ tùng khác nếu xe cần sửa chữa/bảo dưỡng ngoài phạm vi sửa chữa PIN.

Sau đó, thực thành Work Order/Lệnh sửa chữa như quy trình đang chạy.

### 2 Thêm hoạt động tháo PIN trên tab PIN Activity

- Mở Lệnh sửa chữa vừa tạo.
- Chọn tab “PIN Activity”.
- Chọn “Hoạt động sửa chữa mới” động tháo PIN.

*Hình 3. Vào tab PIN Activity và thêm hoạt

### 3 Điền động “10. Tháo PIN kiểm tra tình trạng PIN”

Người dùng như sau:

- Dịch vụ: chọn “10. Tháo PIN kiểm tra tình trạng PIN”.
- Serial: mã serial PIN tin hệ thống/scan thực tế.
- Device Information: bản ghi thông tin PIN hệ thống ghi nhận trên HĐTP theo số Vin.
- Actual Device Information: chọn PIN thực tế đang lắp trên xe tại thời điểm tháo PIN.
- Use Status / Actual Status Device Information: chọn trạng thái thực , ví dụ Good hoặc Broken.
- Thông tin bắt đầu, thúc, khoảng .

**Lưu ý:** Actual Device Information là PIN thực tế đang lắp trên xe tại thời điểm thực hiện tháo PIN.

Trường hợp PIN thực tế đang lắp trên xe khác với PIN đang được ghi nhận trên HĐTP, người dùng cần chọn đúng PIN thực field Actual Device Information để hệ thống cập tin PIN thực tế của xe trước khi thực hiện thanh lý HĐTP.

*Hình 4. Điền thông tin hoạt động tháo PIN và Actual Device Information*

### 4 Lưu và hoàn động tháo PIN

- Sau khi nhập đủ thông tin, chọn Lưu.
- Kỹ /đốc công thực theo thực tế.
- Chọn “Đánh dấu hoàn thành” động tháo PIN hoàn tất.

*Hình 5. Đánh dấu hoàn động tháo PIN*

### 5 Thanh lý 02 PIN 01 Lệnh sửa chữa

Đối với xe , thực hiện lặp lại bước thêm hoạt động PIN đủ 02 hoạt động “10. Tháo PIN kiểm tra tình trạng PIN” sửa chữa.

- Hoạt động thứ nhất: ghi nhận PIN thứ nhất thực tế đang lắp trên xe.
- Hoạt động thứ hai: ghi nhận PIN thứ lắp trên xe.
- Cả hai hoạt đánh dấu Hoàn thành tục đưa lệnh toán.
### 6 Đóng lệnh sửa chữa và hoàn toán

- Sau khi tất cả hoạt PIN đã hoàn thành, thực sửa chữa .
- Thực hiện , hoàn toán lệnh, xuất hóa đơn/thu tiền nếu sinh.
- Đảm bảo trạng thái chữa phải ở hoàn toán thực .

*Hình 6. Lệnh sửa chữa ở trạng thái Hoàn thành thanh toán*

### 7 Thực hiện thanh EMSP và cập nhật trạng thái

1. hệ thống EMSP.
2. Thực hiện chức năng thanh lý HĐTP .

Để thanh lý được , cần thỏa mãn các yêu cầu dưới đây

- Hợp đồng pin đang ở trạng thái Active (đang hoạt động)
- Không có quả pin nào đang ở trạng thái Pending Active trong gói
- Không còn phiên sạc đang chạy
- Không còn nợ bill sạc chưa thanh toán
- Lệnh sửa chữa đã hoàn (kiểm tra qua DMS)

 bước Emsp:

- Truy cập Hệ thống EMSP &gt; Xe máy &gt; — XMĐ
- **Tìm kiếm hợp đồng cần thanh lý:** Nhập VinXe vào ô tìm kiếm và ấn enter. Xác nhận hợp đồng có trạng thái Active
- **Nhấn icon ** : Nhấn biểu tượng thùng rác màu đỏ ở cột Thao Tác. Popup “Thanh lý hợp đồng Pin” xuất hiện
- **Xác nhận thông tin hợp đồng** : tra mã SAP CustomerID, , Ngày kích hoạt, hạn hiển
- ** TRA CÔNG NỢ** : Hệ thống tra nợ cước và phiên sạc

- Nếu bảng Thông tin thanh toán hiển ” nghĩa là Khách hàng không nợ, Cơ sở Hệ thống hiển thu trong bảng Thông tin thanh toán, Cơ sở thông báo Khách hàng và tạo QR để Khách hàng thanh toán.
 - **Kiểm tra Danh sách hợp đồng pin:** Xác nhận đúng mã hợp đồng pin, Serial pin, Mã hợp đồng pin cần thanh lý.
 - **Kiểm tra Mã Showroom &amp; Tên Showroom:** Hệ thống tự điền sẵn.
 - **Nhấn [THANH LÝ HỢP ĐỒNG]:** Xác nhận thao tác. Hệ thống xử lý thành công.

3. thanh , hệ thống .
4. Trên DMS, HĐTP chuyển sang trạng thái “Waitting to terminate”.
### 8 Hướng dẫn chuyển trạng thái Waiting to terminate sang terminated

 cũ, các cơ sở khi chấm dứt HĐ trên EMSP thì sẽ đồng bộ sang DMS. Hợp đồng trên DMS sẽ chuyển sang trạng thái “ **Terminate** ” sở có thể tạo HĐ mới trên Đơn hàng bằng nút “ **Đổi thuê pin** ”.

Tuy nhiên với luồng mới, khi HĐ chấm dứt, hợp đồng trên DMS sẽ chuyển sang trạng thái “Waiting to Terminate” nên sẽ nút Đơn hàng.

Các cơ sở như sau để chấm dứt hoàn toàn HĐTP trên DMS và tạo HĐ mới (mục 6.2 ):

**Bước 1:** Tại màn hình Battery Rental ở trạng thái Waiting to terminate, người dùng chọn tab Contract/s và chọn nút Add new contract management

Hệ thống hiển thị màn hình tạo mới contract management

**Bước 2:** Tại màn hình tạo mới, người dùng chọn :

- Type / Loại: Liquidation / Thanh lý
- Contract status / Trạng thái: Active / Kích hoạt
- Contract date / Ngày HĐ: Ngày ký
- Chọn nút SAVE

**Bước 3:** Người dùng chọn upload file, và tải lên file biên bản thanh lý đã hoàn thành ký và chọn

Sau khi chọn SAVE, người dùng chọn nút Refresh trên ribon để load lại màn hình, link biên bản thanh lý fill vào field File Url. Người dùng có thể xem lại biên bản thanh biên bản thanh lý đã upload local.

File được upload thành công và ở trạng thái Active, bản ghi Battery Rental sẽ chuyển sang trạng thái Terminated. .

Nút “Đổi chủ Hợp Đồng Thuê PIN” trên đơn hàng.

**Trường hợp muốn up biên bản thanh , sở sẽ không thấy HĐTP của cơ sở khác:

Điều hướng dến **Khu vực làm việc &gt; Contract Management &gt; + New** .

Cơ sở điền :

- **Type: Liquidation.**
- **Contract Status: Active.**
- **Contract Date: Ngày kí biên bản thanh lí.**
- **Battery Rental Ref: mã HĐTP.**
- **VIN no: số VIN**

Lưu ý: VIn và Mã HĐTP phải được điền đúng nhau, hệ thống lỗi.

Ấn Lưu để Lưu bản ghi. , cơ sở ấn "Chọn tệp" up giấy tờ:

### 9 lỗi thường gặp &amp;

| **Thông báo lỗi** | **Nguyên nhân** | **Cách xử lý** |
|----------------------------------------------|-----------------------------------------|-------------------------------------------------------------------|
| **Nút [Thanh lý] không hiển thị** | HĐ chưa Active hoặc đã Thanh lý | Kiểm tra trạng thái HĐ. HĐ đang Active. |
| **"Chỉ thanh lý được hợp đồng đang Active"** | HĐ ở trạng thái khác Active | phận kỹ thuật nếu cần điều chỉnh. |
| **Hệ thống chặn ** | 1 quả pin trong gói chưa được kích hoạt | Kích hoạt quả pin PendingActive trước, sau đó thực . |
| **Còn phiên sạc đang chạy** | KH đang có phiên sạc chưa tổng phiên sạc kết thúc tổng hợp lên bill rồi . |
| ** nợ bill sạc chưa thanh toán** | TypeBill 6 hoặc 16 chưa trả | Yêu cầu KH thanh toán nợ sạc trước khi thanh lý. |
| **Chờ lệnh sửa chữa hoàn thành** | DMS còn lệnh sửa chữa chưa đóng | Phối hợp với bộ phận kỹ thuật đóng lệnh sửa chữa rồi thử lại. |

**9. trọng**

**❗ KHÔNG THỂ HOÀN TÁC:** Sau khi nhấn [THANH LÝ HỢP ĐỒNG] và xác nhận thành công, tác. kỹ thông tin xác nhận.

- Chỉ thực từ khách hàng.
- Kiểm tra kỹ VinXe trước khi thực hiện để tránh nhầm hợp đồng.
- Mã Showroom và Tên Showroom phải chính xác — đến phân bổ .
- Khi thanh lý 2 quả pin cùng lúc, đảm lệnh sửa chữa đều đã hoàn thành.
- Thông tin thanh lý sẽ được đồng bộ tự động sang DMS và SAP sau khi hoàn tất.
- Mọi thắc mắc hoặc lỗi ngoài danh sách , vui lòng liên hệ bộ phận IT Support.

## QUY TRÌNH CHUYỂN CHỦ HĐTP XE MAX

Áp dụng khi khách hàng có nhu cầu chuyển quyền thuê Pin sang khách hàng mới.

### 10 tin khách hàng mới trên DMS (Đã có khách hàng chuyển sang bước 2)

### 11 Tạo HĐ chuyển nhượng , truy cập: vực làm việc &gt; Device Information &gt; Battery Information Overview.
- Tìm kiếm theo số VIN của xe cần chuyển chủ.
- Mở bản ghi Device Information và chọn [Chuyển ].

- Tại màn hình New Battery Rental, nhập đầy đủ tin:
- Lý do tạo hợp đồng: , ví dụ “Hợp đồng chuyển ”.
- Lựa chọn loại gói cước: Old package hoặc New package.
- Chọn khách hàng mới nhận chuyển .

- Chọn tab tin thanh toán (Payment Info). ​Chọn loại giao dịch là Refund deposit hoặc Transfer Deposit tùy theo mong muốn của khách hàng là Chuyển cọc hay Hoàn cọc sau đó chọn Save !-- image -->

**Lưu ý:** Đối với xe có 02 Hợp đồng thuê Pin, sau khi Hợp đồng Pin thứ nhất được tạo thành công, hệ thống tạo Hợp đồng Pin thứ hai.

Người dùng cần thực hiện đính kèm Hợp đồng Pin (bao gồm cả hợp đồng được hệ thống tự động tạo) để đảm đều có đầy đủ hồ sơ đính kèm.

Tài liệu bao gồm:

- PL Văn bản tiếp nhận HĐTP XMĐ, Ô tô điện (Đổi chủ xe) T3.2026
- Giấy tờ mua bán có công chứng hoặc photo đăng ký xe đứng HĐTP ký kết giữa ĐLPP
- CCCD hoặc ĐKKD &amp; GUQ của (GUQ trong trường hợp người ký ở bản cứng HĐTP không thống

### 12 Thực hiện chuyển thuê Pin trên EMSP

- Đăng nhập EMSP và thực cũ với Type = .
- Hệ thống tra các điều kiện sau:
- Kiểm tra công nợ , sạc Pin
- Kiểm tra hợp đồng đổi chủ tạo trên DMS (trạng thái Open) và đã Attachment file Scan Hợp đồng, giấy tờ không thỏa mãn điều kiện lỗi Đổi chủ hợp đồng thuê PIN
- Nếu thỏa màn cho phép thanh lý khách hành cũ và Kích hoạt hợp đồng của khách hành mới

**Hướng dẫn chuyển Emsp như sau:**

#### Trường hợp 1: Không có nợ cước (0 VND)

 nợ cước thuê pin, không có phiên sạc đang chạy và DMS đã tạo hợp đồng ảo .

Ảnh 1 :

Ảnh 2:

| **1** | **Mở màn hình Quản lý hợp đồng khách hàng — XMĐ** Vào EMSP &gt; Xe máy &gt; — XMĐ. |
|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **2** | **Tìm kiếm hợp đồng cần thanh lý chuyển chủ** tìm kiếm. Xác nhận hợp đồng của chủ cũ đang ở trạng thái Active. |
| **3** | **Nhấn icon chuyển chủ** Chọn thanh . Popup xác nhận thông tin hợp đồng xuất hiện. |
| **4** | **Xác nhận thông tin hợp đồng** Kiểm tra SapCustomerId, VinXe, ContractNo, ngày kích hoạt hạn. |
| **5** | **Nhấn [KIỂM TRA CÔNG NỢ]** Hệ thống kiểm tra công nợ thuê pin, phiên sạc đang chạy và bill sạc chưa thanh toán. |
| **6** | **Kiểm tra kết quả công nợ** Tổng tiền cần thanh toán là 0 VND điều kiện chặn từ ChargingService. Note: 1. Nếu khách hàng không có bill nợ thuê pin trả trước =&gt; Hệ thống không . 2. Nếu có nợ thuê pin trả trước. Hệ thống tự động tạo bill thuê pin thu tiền của khách hàng. |
| **7** | **EMSP kiểm tra hợp đồng ảo trên DMS** Nhân viên chọn [ ] Hệ thống gọi DMS để xác nhận đã tồn tại hợp đồng ảo hợp lệ cho chủ mới. |
| **8** | **Xác nhận kết DMS** Chỉ tiếp DMS trả về đã có hợp đồng ảo; nếu chưa nối, hệ thống . |
| **9** | **Kiểm tra danh sách pin tin Showroom** Xác nhận đúng hợp đồng pin, Serial pin, mã Showroom và tên Showroom. |
| **10** | **Nhấn [THANH LÝ CHUYỂN CHỦ]** Xác nhận thao tác. Hệ thống xử hoàn . |

✅ **Kết quả: Hợp đồng của chủ cũ chuyển sang trạng thái Thanh lý chuyển (Status = 3). Ngày thanh lý được ghi nhận; sang DMS để tiếp .**

#### Trường hợp 2: nợ cước thuê pin

Áp dụng khi khách hàng còn nợ cước thuê pin. toán; tiếp tục kiểm tra hợp đồng ảo của DMS trước khi cho phép thanh lý chuyển chủ.

*Ví dụ: Hợp đồng hết hạn ngày* ***30/06/2026*** *, khách hàng thanh lý chuyển * ***15/07/2026*** *. EMSP *01 hoặc 02 pin*** *theo trọn kỳ từ* ***01/07/2026 đến 31/07/2026*** *; khách hàng phải thanh toán hoàn .*

| **1** | **Thực hiện các bước 1–5 như Trường hợp 1** Mở màn hình, , kiểm tra thông tin [KIỂM TRA CÔNG NỢ]. |
|---------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| **2** | **Kiểm tra bill truy thu** Hệ thống hiển nợ và tổng số tiền khách hàng cần thanh toán. |
| **3** | **Khách hàng thực ** Khách hàng thanh toán toàn bộ công nợ qua kênh . |
| **4** | **Hệ thống xác nhận thanh toán** Sau khi nhận callback thành công, hệ thống cập nhật trạng thái các bill tục. |
| **5** | **EMSP gọi DMS kiểm tra hợp đồng ảo** Chỉ khi DMS xác nhận đã có hợp đồng ảo , hệ thống mới mở thanh . |
| **6** | **Nhấn [THANH LÝ CHUYỂN CHỦ]** Hoàn tất quy trình. Hợp đồng của chủ cũ chuyển sang trạng thái Thanh lý chuyển . |

**⚠ thu:** Số tiền được số tháng nợ. Ví dụ: 3 tháng nợ x 175.000 VND = 525.000 VND. Tháng lẻ tính theo số ngày thực tế.

#### Các trường hợp đặc biệt

- **Gói thuê có 2 quả pin**

📌 **Quy tắc: , hệ thống xử lý 2 . Việc thanh lý chuyển thực ảo trên DMS bao phủ đúng .**

- **Thanh lý 2 quả cùng lúc:**

- Hệ thống kiểm tra hợp đồng ảo trên DMS cho từng quả pin cần chuyển giao.
- Cả 2 thanh lý chuyển đều được ghi nhận hợp lệ trong hợp đồng ảo của .
- Hợp đồng KH sang trạng thái Thanh lý chuyển (Status = 3), BatteryContracts = [].
- DMS nhận kết tương ứng.

- **Kiểm tra hợp đồng ảo trên DMS**

 chấm dứt hợp đồng của chủ cũ, EMSP tự động gọi sang DMS để kiểm tra hợp đồng ảo đã được .

- Nếu DMS chưa có hợp đồng ảo, chưa hợp lệ hoặc DMS không phản hồi: Hệ thống chặn thanh lý chuyển hoàn ảo trên DMS.
- Nếu DMS xác nhận đã có hợp đồng ảo hợp lệ: Hệ thống tục và hoàn thanh .

⚠ **Lưu ý: Nhân viên cần phối hợp với bộ phận DMS để hoàn ảo cho trước khi thực .**

- **Phiên sạc đang chạy hoặc nợ bill sạc**
| **Phiên sạc đang chạy** | Hệ thống ChargingService phát hiện phiên chưa tổng hợp → Chặn thanh lý. Chờ phiên sạc kết thúc. |
|--------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Nợ bill sạc (TypeBill 6/16)** | Hệ thống phát hiện nợ sạc chưa thanh toán → Chặn thanh lý. toán bill sạc trước. |
| **Không còn phiên, không nợ sạc và đã có hợp đồng ảo** | Hệ thống luồng thanh . |

 lỗi , ĐLPP gửi email cho

- **Kích hoạt chủ mới sau thanh lý chuyển chủ**

Áp dụng sau khi hợp đồng của chủ cũ đã chuyển sang trạng thái Thanh lý chuyển tục đồng bộ hợp đồng của sang EMSP.

1. DMS đồng bộ hợp đồng của sang EMSP trên cơ sở hợp đồng ảo đã được xác nhận trước đó.
2. NV thực hiện thanh toán trên EMSP Portal, chọn số tháng toán.
3. Hệ thống gen bill đúng (quả 1: 175.000/tháng, quả 2: 125.000/tháng).
4. Hệ thống cho phép Active hợp đồng với .

**💡 Gợi ý:** Nếu Active 2 quả không đồng thời, hệ thống tự căn chỉnh số tháng của quả thứ 2 để khớp dueDate với quả thứ 1.

​ **Lưu ý:**

- HĐTP của chủ cũ chuyển trạng thái Terminated / Đã thanh cọc thuê pin ở DMS và SAP cùng . tin Transfer Or Refund cũ là Yes
- Trường hợp cọc pin ở DMS và SAP không khớp, HĐTP của chủ cũ ở trạng thái Waiting to terminate Transfer Or refund chủ cũ là No
- Trường hợp cọc pin không khớp, cơ sở cần kiểm tra lại thông tin sau đó chọn Transfer Or Refund = Yes chuyển trạng thái HĐTP của chủ cũ là Terminated / Đã thanh lý

### 13 cọc cũ ở trạng thái Terminated / Đã thanh lý, hệ thống phê duyệt ở trạng thái Open / Mở. Yêu cầu được Hoàn cọc hay Chuyển cọc phụ thuộc vào lựa chọn của cơ sở trên màn hình HĐTP của Bước 2

- Người dùng đính kèm file hành DPR gửi QLV phê duyệt.
- Sau khi DPR được , HĐTP tương ứng được chuyển sang trạng thái Active/Đang hoạt động.
### 14 thông báo lỗi thường gặp &amp;

| **Thông báo lỗi** | **Nguyên nhân** | **Cách xử lý** |
|---------------------------------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Nút [Thanh lý] không hiển thị** | Hợp đồng chưa Active hoặc đã Thanh lý chuyển | Kiểm tra trạng thái hợp đồng. Chỉ hợp đồng Active mới được thực . |
| **“ chuyển hợp đồng đang Active”** | HĐ ở trạng thái khác Active | Liên hệ bộ phận kỹ thuật nếu cần điều chỉnh. |
| **Hệ thống chặn ** | 1 quả pin trong gói chưa được kích hoạt | Kích hoạt quả pin PendingActive trước, sau đó thực . |
| **Còn phiên sạc đang chạy** | KH đang có phiên sạc chưa tổng hợp | Chờ phiên sạc kết thúc tổng hợp lên bill rồi . |
| ** nợ bill sạc chưa thanh toán** | TypeBill 6 hoặc 16 chưa trả | Yêu cầu khách hàng thanh toán nợ sạc trước khi thanh lý chuyển . |
| **Chưa có hợp đồng ảo của chủ mới** | DMS chưa tạo hợp đồng ảo, chưa hợp lệ hoặc DMS không phản hồi | Hoàn tất việc tạo hợp đồng ảo trên DMS và thực hiện kiểm tra lại trước khi thanh lý chuyển . |

### 15 trọng

❗ **KHÔNG THỂ HOÀN TÁC: nhấn [THANH LÝ CHUYỂN CHỦ] và xác nhận thành công, sẽ chuyển sang trạng thái Thanh lý chuyển . kỹ VIN, nhận hợp đồng ảo trên DMS trước khi thực hiện.**

- Chỉ thực xác nhận trên DMS.
- Kiểm tra kỹ VinXe trước khi thực hiện để tránh nhầm hợp đồng.
- Mã Showroom và Tên Showroom phải chính xác — đến phân bổ .
- Khi thanh lý 2 quả pin cùng lúc, đảm ảo của DMS đã bao phủ đầy đủ các quả pin cần chuyển giao.
- Sau khi hoàn tất, cũ được cập sang trạng thái Thanh lý chuyển ; sang DMS hệ thống.
- Mọi thắc mắc hoặc lỗi ngoài danh sách , vui lòng liên hệ bộ phận IT Support.

## QUY TRÌNH KÍCH HOẠT HĐTP CỦA PIN 2

**Bước 1.** Tạo lệnh sửa chữa và thực động lắp Pin 2 cho thuê

- WO ở trạng thái lệnh sửa chữa/released -&gt; tab Pin activity -&gt; New WO service activity -&gt; hoạt động Pin 14 (Pin đã kích hoạt thái unlease/at BU)
- Sau khi điền đủ thông tin bấm Save để lưu hoạt ; complete hoàn động Pin
- Chuyển WO sang trạng thái Invoiced.

**Bước 2.** Tạo và kích hoạt HĐTP cho Pin 2 (Pin thuê)

- Mở bản ghi device information theo serial Pin đã thực hiện xong hoạt động 14 -&gt; “HĐ Pin 2”
- Điền thông tin Lựa chọn loại gói cước, , Battery Option trên form HĐ mới -&gt; Save

- Thêm Package Type, đính kèm hồ sơ và phát hành phiếu thu cọc (nếu có).
- Kích hoạt gói cước

## KÍCH HOẠT LẠI HĐTP CHO VINXE ĐÃ THỰC HIỆN THANH LÝ PIN VỀ VINFAST

Để thực hiện Kích hoạt lại hợp đồng thuê PIN,

Đầu tiên cần tạo Lệnh sửa chữa (LSC) để lắp PIN lên xe để thực **Bước 1: Lệnh sửa chữa (LSC) **

**Cố vấn chọn , tiến hành thêm thông tin sửa chữa bắt buộc), , khách hàng và , *

**Bước 1.1:** dung sửa chữa Tháo lắp PIN

Cố vấn thêm dung sửa chữa thay thế PIN đã bán cho khách

Giao diện danh sách dung và phụ tùng hiển thị

Đối với nội dung sửa chữa, “ **09- Sửa chữa PIN** ”. Chọn mã công việc lắp pin vấn thể thêm các dịch vụ và phụ tùng khác nếu xe cần sửa chữa/bảo dưỡng ngoài phạm vi thay PIN

Sau đó, thực thành Work Order/Lệnh sửa chữa như quy trình đang chạy.

**Bước 1.2: động sửa chữa, Tháo PIN và Lắp PIN tra**

- 1.1. **Thêm hoạt động** “ **12. Lắp PIN cho thuê trước khi kích hoạt HĐ”**

CVDV thêm hoạt chữa tháo PIN của khách. Vào **mục Pin Activity** --&gt; **Hoạt động *

Màn hình thêm hoạt , <!-- image -->

- **Dịch vụ** : Chọn  “ **12. Lắp PIN cho thuê trước khi kích hoạt HĐ** ”
- **Serial PIN** : Tự động fill serial PIN khách đang thuê vào, KTV có thể scan lại mã PIN
- **Use status:** Nhập trạng thái . Tốt (good) hoặc Hỏng (broken)
- **Kĩ thuật viên** : Chọn KTV để giao việc
- **Khoang sửa chữa** : sửa chữa

- **Thông tin lịch trình** : Chọn thông tin chữa

- **Lưu ý** : sản PIN mới thuê

Sau khi hoàn thành, nhấn chọn **Lưu.**

Kĩ thuật viên thực hiện tháo PIN, đốc công sẽ đóng hoạt tháo thành công

- 1.2. **Thêm hoạt động sửa chữa “13. Tháo PIN khỏi xe HĐ”** (chỉ thực hiện nếu không có nhu cầu gắn PIN để kích hoạt nữa hoặc muốn lắp PIN khác)

CVDV thêm hoạt chữa Lắp PIN mới cho khách. Vào **mục PIN Activity** --&gt; **Hoạt động *

Màn hình thêm hoạt , <!-- image -->

- **Dịch vụ** : Chọn **13. Tháo PIN khỏi xe HĐ**

- **Serial** : Kĩ thuật viên Scan serial PIN
- **Use status:** Nhập trạng thái . Tốt (good) hoặc Hỏng (broken)
- **Kĩ thuật viên** : Chọn KTV để giao việc
- **Khoang sửa chữa** : sửa chữa
- **Thông tin lịch trình** : Chọn thông tin chữa

Sau khi hoàn thành, nhấn chọn **Lưu.**

Kĩ thuật viên thực hiện lắp PIN, CVDV sẽ đóng phiếu sau khi PIN lắp thành công

**c) Dừng kích hoạt hoạt động Pin Activity**

Chọn Dừng kích hoạt động Pin Activity

Theo thứ tự:

**12. Lắp PIN cho thuê trước khi kích hoạt HĐ**

**13. Tháo PIN khỏi xe HĐ (nếu có)**

**Bước 2: Đóng lệnh sửa chữa**

Sau khi Tất cả các Hoạt động sửa chữa , thực như quy trình đã chạy, bao gồm:

- toán

- Xuất hóa trình Claim (đối với hành)

**Bước 3: PIN lại**

Vào phần mềm DMS chọn Phân hệ **Khu vực làm việc &gt; Device Information &gt; Battery Informaition Overview** sS

- Tìm kiếm VIN xe cần Kích hoạt lại hợp đồng thuê PIN
- **Tại màn hình chi tiết Device information &gt; Nhấn [Thuê lại HD]**
- Tại màn hình Battery Rental Mới
 - Chọn Contract Tpye (nếu trường hợp VIN xe cước)
- **Sau đó chọn [Lưu]**
- Tiếp tục chọn tab **[** Attachment file] để đính kèm các file , giấy tờ !-- image -->
 - **Ở bước này, nếu KH thuê Pin không ban đầu, ĐLPP điền mã KH của **

**Bước 4:** Thực hiện Kích hoạt hợp đồng thuê PIN