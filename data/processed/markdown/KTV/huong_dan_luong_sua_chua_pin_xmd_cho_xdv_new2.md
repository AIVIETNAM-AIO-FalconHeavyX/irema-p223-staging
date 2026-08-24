---
document_id: KTV002
title: Hướng dẫn luồng sửa chữa Pin XMĐ cho XDV new2
source_file: Hướng dẫn luồng sửa chữa Pin XMĐ cho XDV_new2.xlsx
source_path: KTV/Hướng dẫn luồng sửa chữa Pin XMĐ cho XDV_new2.xlsx
document_type: xlsx
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

# Hướng dẫn luồng sửa chữa Pin XMĐ cho XDV new2

HƯỚNG DẪN LUỒNG SỬA CHỮA PIN XE MÁY ĐIỆN

| Bước 1 | Tiếp nhận & phân loại lỗi | Tiếp nhận & phân loại lỗi | Thời gian tối đa | Link/ Quy định dẫn chứng |
|----------|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| | 1.1 | phiếu tiếp nhận và ghi nhận lỗi KH phản ánh. tin của | D | D : Ngày phát sinh |
| | 1.2 | Đánh giá tình trạng lỗi trên xe theo các HD trên hệ thống STP số 823VNSC002 - Nếu xác định được sẽ sửa chữa vận chuyển 2 chiều. PYTES gửi . - Nếu chưa xác định được có bảo hành hay không thì với KH cần PYTES kiểm tra và xác nhận lỗi cụ thể. | D | xác nhận lỗi pin LFP Mục " HƯớng dẫn" trong sheet " tin" |
| | 1.3 | - Khảo sát nhu cầu mượn pin (đối với KH Pin mua). đầy đủ. - Pin của GSM không . | D | Lưu ý: , cần thông tin rõ với KH về trả cp sửa chữa nếu NCC thông tin lỗi đến từ KH. |
| | 1.4 | Pin của VinEG: B1/B2/P1S/D1/LFP 3.5KWH - Lấy file Log CAN (Nếu không lấy được Can log, thì đo điện áp 2 cực). - Mô tả lỗi cụ thể của Pin (trong body mail) , hiện tượng lỗi khi nào, tần suất lỗi,..+ sheet KSKH | D | |
| | 1.5 | Pin PYTES: 1.0KWH, 1.2KWH, 2.4KWH & 1.5KWH - Làm BCKT (không cần chụp ảnh xe) Thực hiện đo điện áp 2 cực. Video hoặc hình ảnh chứng minh lỗi. | D | |
| | 1.6 | - Với pin VinEG -> chuyển sang chuyển sang (không có LĐC) | D | |
| Bước 2 | Gửi mail sửa chữa | Gửi mail sửa chữa | | |
| | 2.1 | Mở Lệnh sửa chữa (WO) | D | |
| | 2.2 | Cập nhật thông tin đầy đủ vào sheet "1. XDV nhập liệu" ( copy trong file " chữa Pin XMĐ online " sang ) | D | 1. XDV nhập liệu'!A1 |
| | 2.3 | Gửi mail yêu cầu sửa chữa theo sheet "2. Form gửi email", Gửi kèm tiệp đã đề cập ở Bước 1.4 , 1.5. : Gửi Đúng đầu mối NCC, email phối pin và DV sửa chữa pin xmđ & QLV phụ trách XDV của mình. | D | 2. Form gửi email'!A1 |
| | 2.4 | VinEG / NCC PYTES sẽ phản hồi Phương án sửa chữa & báo giá hoặc sửa bảo hành qua mail Trong vòng tối đa 2 ngày | D+1 | |
| | 2.5 | cầu sửa chữa lên Link ( bắt buộc 100% sau khi có xác nhận của NCC ) | | [PIN] KHAI BÁO SỬA CHỮA PIN XMĐ |
| | 2.6 | link theo dõi tiến chữa lấy tin. | | Theo dõi sửa chữa Pin XMĐ online.xlsx |
| | 2.7 | Sau khi có phản hồi của NCC, XDV trao đổi với KH để thống nhất phương chữa xác nhận đồng ý / không đồng ý qua email cho NCC 24h. | D+2 | |
| Bước 3 | pin về NCC sửa chữa | pin về NCC sửa chữa | | |
| | 3.1 | Tháo Pin khỏi xe. Vệ sinh Pin sạch sẽ, không bùn đất bám chặt trên Pin trước khi gửi đi. | D+3 | |
| | | Với Pin LFP 3.5 kWh: Khi có dấu hiệu nứt nắp, nước vào hoặc phát nhiệt bất thường -> 100% thực hiện tháo BMS theo hưỡng dẫn trên STP | D+3 | Mục " Hướng dẫn tháo BMS " trong Sheet " Thông tin " |
| | | Tháo Pin khỏi xe. Vệ sinh Pin sạch sẽ, không bùn đất bám chạt trên Pin trước khi gửi đi. | D+3 | Mục " Hướng dẫn tháo BMS " trong Sheet " Thông tin " |
| | 3.2 | - Tạo Lệnh điều chuyển (đối với dòng pin LFP 3.5). - dòng pin DMS không cần tạo LĐC. -> Gửi mail ĐVVC kèm Lệnh Điều chuyển | D+3 | Chỉ cần gửi LĐC qua email theo loop mail sửa chữa. |
| | 3.3 | Với Pin mua: Pin (nếu KH có nhu cầu), kí HĐ cho mượn (Đính kèm) : + Nếu lỗi từ : email cho DV Thuê pin xmđ tục đền bù. + Nếu lỗi sản phẩm ( hành ): XDV đổi cho KH 1 quả pin kí từ Điều phối pin điều về | D+3 | Mục "Form biểu mẫu" trong Sheet " Thông tin " |
| | 3.4 | Đối với Pin PYTES, team NCC sẽ phản hồi pin cần phân tích lỗi hoặc không tích lỗi: -	Nếu cần phân tích: ĐLPP/XDV họ đến trực tiếp ĐLPP/XDV kiểm tra Pin và xe. -	Nếu không cần phân tích: mail chuyển trực Pytes Tây Ninh (CÔNG TY TNHH NĂNG LƯỢNG PYTES VIỆT NAM_Người nhận: Trần Thị Kim Soan_Địa : Lô G3-1, đường D3, KCN Việt Hóa - Đức Hòa III, xã , tỉnh , điện thoại: ) | | Lưu ý: XDV nên repmail với NCC PYTES bằng |
| | 3.5 | PYTES team sẽ phản hồi xử lỗi (1 trong 2): 1. Nếu sửa BH: Pytes sẽ sửa ~ 8-10 ngày ( theo HD ), XDV có thể cho KH mượn chờ xử lý. 2. Nếu ngoài BH: Pytes sẽ gửi báo giá sửa chữa -> XDV/KH xác nhận với báo giá trong vòng 24h -> Pytes tiến hành sửa chữa. | | |
| | 3.6 | Khi ĐVVC tới thu gom pin đi sửa : XDV cùng Kiểm tra hiện trạng cùng ĐVVC và kí 02 BBBG do ĐVVC cung cấp. (1 bản ĐVVC giữ , 1 bản XDV lưu) | D+4 | |
| | 3.7 | Với TH khách hàng trả phí : - Sau khi nhận được báo giá Sửa chữa + báo giá vận chuyển 2 chiều => XDV làm KH để yêu cầu thanh toán. - Repmail kèm hình ảnh kết quả giao . | Thanh toán trước thời điểm trả pin | Lưu ý : XDV có trách nhiệm yêu cầu KH phải thanh toán xong thì mới được phép trả pin sửa chữa cho KH |
| Bước 4 | Hoàn thành sửa chữa | Hoàn thành sửa chữa | | |
| | 4.1 | Với TH Pin Mua : chữa xong và XDV nhận lại, XDV tháo pin mượn & kết thúc (nếu có) và của khách hàng. | gian sửa chữa thực tế | Lưu ý: Pin Mượn được XDV để kí gửi hoặc XDV có thể phận Điều phối Pin |
| | 4.2 | Với TH Pin Thuê : Pin thuê sau khi sửa chữa xong tại NCC, Điều phối pin sẽ chuyển trả lại XDV. | gian sửa chữa thực tế | Thời gian sửa chữa VinEG dự kiến: -	Hư hỏng thông thường: 4 ngày/pack -	Hư hỏng nặng: 7~14 ngày/pack tùy theo tình trạng cụ thể Thời gian SC pin Pytes: ~ 8-10 ngày ( theo HD ) Lưu ý : Thời gian sửa chữa NCC nhận được Pin thực tế |
| | 4.3 | XDV Hoàn thành tục giấy tờ khác theo XDV để thanh toán, QTSC, ĐXBH, LSC | Theo thời gian sửa chữa thực tế | Thời gian sửa chữa VinEG dự kiến: -	Hư hỏng thông thường: 4 ngày/pack -	Hư hỏng nặng: 7~14 ngày/pack tùy theo tình trạng cụ thể Thời gian SC pin Pytes: ~ 8-10 ngày ( theo HD ) Lưu ý : Thời gian sửa chữa NCC nhận được Pin thực tế |

| [PIN] KHAI BÁO SỬA CHỮA PIN XMĐ |
|---------------------------------------|
| Theo dõi sửa chữa Pin XMĐ online.xlsx |

| Hạng mục sửa chữa | Thời gian sửa chữa | |
|---------------------------------|-------------------------------------------------|---------------------------------------------|
| Hạng mục sửa chữa | (ngày ) | |
| Sửa chữa pin   () | 9 đến 23.5 ngày | Sửa chữa pin nặng phải đưa về trung tâm SC. |
| Sửa chữa pin   () | (KH được mượn pin trong thời gian chờ sửa chữa) | - Tìm phương chữa: 1 ngày |
| Sửa chữa pin   () | | - Vận chuyển: 2-10 ngày |
| Sửa chữa pin   () | | - Tiến hành sửa chữa: 5-11.5 ngày |
| Sửa chữa pin   () | | - Lắp lên xe KH: 1 ngày |

THÔNG TIN CHUNG

| Loại | Nhà cung cấp pin | Email |
|------------------------|--------------------------------------|------------------------------------------------------------------------------------------------------------------|
| Đầu mối nhận Thông tin | NCC PYTES | ; ; ; |
| mối nhận Thông tin | VinEG | , , |
| mối nhận Thông tin | | ; ; |
| mối nhận Thông tin | Điều phối sửa chữa | ; |
| mối nhận Thông tin | Vận chuyển & Phê duyệt mượn, đổi pin | ; Hoặc |

| Link | Link sửa chữa | [PIN] KHAI BÁO SỬA CHỮA PIN XMĐ |
|---------|--------------------------------------------|---------------------------------------|
| Link | Link Theo dõi tiến chữa tại nhà máy | Theo dõi sửa chữa Pin XMĐ online.xlsx |
| Link | QR Code | |

<!-- image -->

| Form ( ) | Hợp đồng pin XMD |
|----------------------|----------------------------------------------|
| Form ( ) | Ban cam ket chi tra chi phi pin thue bi hong |

| Hướng dẫn | xác nhận lỗi pin LFP |
|-------------|----------------------------------------------------|
| Hướng dẫn | BMS |

| No | dung | Mã phụ tùng | Loại pin | Dung lượng |
|------|--------------------------------------------|---------------|------------|--------------|
| 1 | Code đổi pin LFP (BAT1200600**********) | BAT12006000 | LFP | 3.5kWh |
| 2 | Code đổi pin B1 (DRT00002386-************) | DRT00002386 | B1 | |
| 3 | Code đổi pin B2 (BAT120110********) | BAT12011000 | B2 | |
| 4 | Code đổi pin D1 (BAT120100******) | BAT12010000 | D1 | 2.0 kWh |
| 5 | Code đổi pin P1S (DRT00003498) | DRT00003498 | P1S | |
| 6 | Code đổi pin 2.4KWH (BAT00000001AA) | BAT00000001 | Pytes 2.4 | 2.4 kWh |
| 7 | Code đổi pin 1.2KWH (BAT00000002AA) | BAT00000002 | Pytes 1.2 | 1.2 kWh |
| 7 | Code đổi pin 1.5KWH (BAT00000010AA) | BAT00000010 | Pytes 1.5 | 1.5 kWh |

| XDV Điền Mã LSC vào đây |
|---------------------------|

<!-- image -->

| Link |
|---------|
| QR code |

| https://forms.office.com/Pages/ResponsePage.aspx?id=OSlq7VPRkk-U-D15DZbJ-KQlqdE8GXZPtDqG5Bqp69RUNE40MTUzOTBJRk83MkRHSkdCSUVKVEhYRSQlQCN0PWcu |
|------------------------------------------------------------------------------------------------------------------------------------------------|

| Bước 1 |
|----------------------------|
| Người Nhận mail (Bắt buộc) |
| Người Nhận mail (Bắt buộc) |
| Người Nhận mail (Bắt buộc) |
| Người Nhận mail (Bắt buộc) |

| Copy hoặc chọn LSC WO vào ô E3 | : | S44901-WO-25-11-23-002 |
|----------------------------------|-----|------------------------------------------------------------------------------------------------------------------------------|
| NCC PYTES | : | ; ; ; |
| NCC Pin VinEG | : | , , |
| Team Pin | : | ;; Hoặc |
| QLV (email của ) | : | |

| VinEG |
|---------|

| Tiêu đề mail |
|--------------------|
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |
| dung thân mail |

| Nxxxxx_Sửa Pin VinEG_RLLVxxxxxx_BATxxxxxxx_Có/Không |
|-------------------------------------------------------------------------------------------------------------------|
| Dear Team VinEG |
| , all related team- ntt/fyi |
| Our workshop would like to send information of repair battery. Please check & feedback solution repair/ quotation |
| dung yêu cầu |
| Code |
| Tên Đại lý |
| Họ và tên người giao/nhận Pin |
| SĐT người giao/nhận Pin |
| Địa chỉ người giao nhận Pin |
| Số khung xe/VIN xe |
| QR mã serial pin dài 32 ký tự |
| Lỗi cụ thể của Pin? |
| Pin của khách hàng là Pin thuê hay mua? |
| Loại hình sửa chữa |
| Cơ sở còn Pin kí gửi tại XDV hay không |
| Khách hàng có cần mượn/đổi pin hay không? |
| Nếu XDV còn Pin kí thì điền rõ QR pin |
| Nếu XDV còn Pin kí thì điền rõ QR pin |
| Lệnh điều chuyển () |
| Pin có phải của tài xế GSM không ? |
| Ngoại quan pin vỡ  không ? |
| Ngoại quan pin vỡ  không ? |

| XDV Cập tin |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Nxxxxx |
| VF Huy Hiệu Ô Chợ Dừa |
| A |
| |
| 686 Nguyễn Chí Thanh, Phường Đông Thọ, TP. |
| RLLVxxxxxx |
| BATxxxxxxx |
| VD: nhiệt, Không lên nguồn, Lệch điện áp cell, …. |
| XDV check Device information DMS để check trạng thái pin mua hay thuê |
| Pin sửa chữa hành hay khách hàng thanh toán? |
| Có/Không |
| Có/Không |
| Cơ sở điền mã QR pin tồn tại XDV (Nếu XDV không điền mã Pin mượn, Điều phối pin không Phê duyệt , thất thoát Pin XDV sẽ phải đền bù) |
| Cơ sở điền mã QR pin tồn tại XDV (Nếu XDV không điền mã Pin mượn, Điều phối pin không Phê duyệt , thất thoát Pin XDV sẽ phải đền bù) |
| Lệnh điều chuyển () - Bắt buộc ( Không có không ) |
| Có/Không |
| TH bị nứt : Ghi rõ “ Pin Nứt Topcase , đã tháo rời mạch BMS và bọc túi chống sóc kèm túi ốc riêng  “, đảm , bọc đúng tiêu chuẩn của VF |
| TH không nứt : Ghi rõ “Pin không nứt , không cần tháo BMS” |

| THank you ! |
|---------------|

| | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link | theo Link |
|----|------------------------------|----------------------|----------------------------|----------------------|----------------------|--------------------------------------|----------------------|--------------------------------------------|----------------------|-----------------------------------------------------------------------------|-----------------------|---------------------------------------------|----------------------|----------------------|-----------------------------------------|-------------------------------------------|--------------------------------------------------------------------------------------|------------------------------------|----------------------------------|-------------------------------------|
| ID | Số WO  ( Số Lệnh sửa chữa ) | Tên Đại Lý | Code đại lý ( : S33006 ) | Dòng xe | Km xe | việc vs GTSC ( Nếu có ) | Nhà cung cấp pin | VIN ( Số VIN của Xe  - RPXP1LHHVRE007061 ) | Loại Pin | Serial Pin (Mã Pin dài )  Ví dụ: DRT00002386-AN4300--000082-01-001 | Loại hình sửa chữa | Lỗi Pin  (vd :, nguồn,,..) | Dòng Pin | Tên người giao/nhận | XDV có sẵn pin dự trữ cho KH không | Khách hàng có cần mượn/đổi pin hay không? | Lệnh điều chuyển DMS( Đối với pin không điều chuyển trên DMS ghi số 0 ) | Email người nhận tại XDV | SĐT người nhận tại Xưởng dịch vụ | |
| 1 | S44901-WO-25-11-23-002 | VinFast Quang Thành | S44901 | Evo200 | 75649 | 30234 | VinEG | RPXP1LHHVPE061180 | Pin mua | BAT12006000090003094231009D00199 | Sửa chữa | ĐANG CHẠY THÌ LÊN GA TỐI ĐA CHỈ 30KM/H | LFP | | Có | Không | 2025-11-24-0086 | | | 856 , , Q.12 |
| 2 | N52001-WO-25-11-25-001 | VinFast Quang Thành | S44901 | Evo200 | 8.019 | KHÔNG | VinEG | RPXP1LHHVPE069827 | Pin mua | BAT12006000090003094231026D00267 | Sửa chữa | Xe bị hạn chế tốc chuyển | LFP | | Có | Có | 2025-11-25-0117 | | | 856 , , Q.12 |
| 3 | S32402-WO-25-11-24-005 | VinFast Quang Thành | S44901 | Evo200 | 1000 | KHÔNG | VinEG | RPXP1LHHVNE056350 | Pin mua | BAT12006000020003094221109N00041 | Pin Sửa chữa | Lỗi 11, cảm biến nhiệt không cân bằng | LFP | | Có | Có | 2025-11-26-0041 | | | 856 , , Q.12 |
| 4 | S32811-WE-25-11-26-003 | VinFast Quang Thành | S44901 | Evo200 | 2000 | KHÔNG | VinEG | RPXP1LHHVNE064447 | Pin Thuê | BAT12006000100003094240409D00287 | Pin Sửa chữa | QUÁ NHIỆT CELL KHI XÃ | LFP | Hậu | Không | Không | 2025-11-26-0056 | | | 856 , , Q.12 |
| 5 | S32402-WO-25-11-26-001 | VinFast Quang Thành | S44901 | Evo200 | 500 | KHÔNG | VinEG | RPXP2LHLVRE032202 | Pin Thuê | BAT12006000120003094240917D00069 | Pin Sửa chữa | vỏ, lỗi số 97 | LFP | Hậu | Có | Có | 2025-11-26-0065 | | | 856 , , Q.12 |

| BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY |
|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY |
| BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY | BIÊN BẢN VẬN CHUYỂN/ HƯ HỎNG SỬA CHỮA PIN PAPER OF TRANSPORTATION/ REPARING BATTERY |

| I. THÔNG TIN CHUYỂN PHÁT |
|----------------------------|

| Giao/nhận: giờ ….. / ….. ; Ngày ..... / ….. / 2025 | Giao/nhận: giờ ….. / ….. ; Ngày ..... / ….. / 2025 |
|------------------------------------------------------|------------------------------------------------------|

| Sender | Sender | Email | Phone | Địa chỉ/ address | Địa chỉ/ address | Địa chỉ/ address |
|------------|------------|---------|-----------|------------------------------------------------------|------------------------------------------------------|------------------------------------------------------|
| A | A | 0 | | 686 Nguyễn Chí Thanh, Phường Đông Thọ, TP. | 686 Nguyễn Chí Thanh, Phường Đông Thọ, TP. | 686 Nguyễn Chí Thanh, Phường Đông Thọ, TP. |

| Loại hình Pin | Loại hình Pin | Loại chi phí | Lệnh chuyển Pin | WO | WO | WO |
|--------------------------------------------------|--------------------------------------------------|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|------------------------|------------------------|
| Pin sửa chữa hành hay khách hàng thanh toán? | Pin sửa chữa hành hay khách hàng thanh toán? | Có/Không | TH bị nứt : Ghi rõ “ Pin Nứt Topcase , đã tháo rời mạch BMS và bọc túi chống sóc kèm túi ốc riêng  “, đảm , bọc đúng tiêu chuẩn của VF | S44901-WO-25-11-23-002 | S44901-WO-25-11-23-002 | S44901-WO-25-11-23-002 |

| II. THÔNG TIN SỬA CHỮA |
|--------------------------|

| Model | Km xe | Serial Pin | Serial Pin | Tên Lỗi/ faulty symtom | Tên Lỗi/ faulty symtom | Tên Lỗi/ faulty symtom |
|---------|---------|--------------|--------------|---------------------------|---------------------------|---------------------------|
| ? | ? | BATxxxxxxx | BATxxxxxxx | Có/Không | Có/Không | Có/Không |

| III. XÁC NHẬN KIỂM TRA HIỆN TRẠNG KHI GIAO NHẬN |
|---------------------------------------------------|

| vị trí cần tra | vị trí cần tra | 2 xác nhận | 2 xác nhận |
|------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|------------------------------|------------------------------|
| Vỏ pin ( , rơi vỡ móp méo không?) | Vỏ pin ( , rơi vỡ móp méo không?) | | |
| Mạch BMS có bọc riêng và đảm ? ( trong TH tháo BMS) ( có bọc lẫn với ốc vít không , có bọc túi chống sốc không ?) | Mạch BMS có bọc riêng và đảm ? ( trong TH tháo BMS) ( có bọc lẫn với ốc vít không , có bọc túi chống sốc không ?) | | |
| Tình trạng giắc connector ( , méo, vỡ không ?) Tình trạng cực (- + ) connector | Tình trạng giắc connector ( , méo, vỡ không ?) Tình trạng cực (- + ) connector | | |
| Số Khắc QR code có bị mờ ? | Số Khắc QR code có bị mờ ? | | |
| tình trạng khác ( nếu có ) | tình trạng khác ( nếu có ) | | |
| Ghi chú: BBBG được in 2 bản, một bản bên A giữ , bên B giữ, xác nhận việc hoàn thành nghĩa vụ bàn giao | | | |
| Tích X vào ô tương ứng để xác nhận hiện trạng thực | | | |

| Ghi chú bất thường / hư hỏng nếu có | Ghi chú bất thường / hư hỏng nếu có |
|-----------------------------------------------|-----------------------------------------------|
| Vỏ bị nứt 2 vị trí | Vỏ bị nứt 2 vị trí |
| Không đạt, bọc lẫn ốc vít, có đạt, bọc lẫn ốc vít, có |
| Connector bị gãy 1 chân | Connector bị gãy 1 chân |
| Mờ hết QR code | Mờ hết QR code |
| Ví dụ : PIn có dấu hiệu độ chế, hoặc .... | Ví dụ : PIn có dấu hiệu độ chế, hoặc .... |

| giao (A) | nhận (B) |
|----------------|----------------|

| Ký và ghi họ tên | Ký và ghi rõ họ tên |
|--------------------|-----------------------|

| CÂU HỎI | ĐÁP ÁN |
|----------------------------------------------------------------|----------|
| Câu 1: Bước đầu tiên trong quy trình xử lỗi là gì? | B |
| A. Sửa chữa ngay | B |
| B. Tiếp nhận & phân loại lỗi gửi mail sửa chữa cho NCC | B |
| C. Gửi về nhà | B |
| D. Báo khách hàng ngay là lỗi pin | B |
| Câu 2: Điều kiện quan trọng khi xác định lỗi pin VinEG là gì? | |
| hóa | B |
| B. Có log CAN & KSKH | B |
| video lỗi | B |
| phiếu | B |
| Câu 3: khách mượn pin ? | |
| A. Khi khách có nhu cầu | A |
| B. Sau khi ký BB bàn giao | A |
| C. Không bao giờ | A |
| chưa | A |
| Câu 4: Gửi email sửa chữa kèm theo gì? | |
| A. Chỉ mô tả lỗi | B |
| B. File chứng minh lỗi + form thông tin trong body mail | B |
| C. Không cần file | B |
| D. Hóa đơn bán pin | B |
| Câu 5: Thời gian phản hồi mail của NCC thường là? | |
| A. D+0 | B |
| B. D+1 | B |
| C. D+2 | B |
| D. D+3 | B |
| Câu 6: được link sửa chữa? | |
| B |
| B. Sau xác nhận NCC | B |
| tiếp nhận khách hàng | B |
| | B |
| Câu 7: Khi tháo pin khỏi xe cần làm gì? | |
| A. Ngâm nước pin | C |
| B. Đóng gói ngay giao cho vận chuyển | C |
| C. Vệ sinh sạch sẽ ngoại quan pin | C |
| nguyên bản | C |
| Câu 8: Pin LFP 3.5kWh cần xử lý gì nếu có dấu hiệu bất thường? | |
| A. Để nguyên bản | D |
| B. Tất cả đều tháo nắp | D |
| C. Ngâm nước | D |
| D. Tháo BMS, loại bỏ nước (nếu có) nứt vỡ | D |
| Câu 9: Thời gian sửa chữa PYTES (BH) là? | |
| A. 1–2 ngày | C |
| B. 3–5 ngày | C |
| C. 8–10 ngày | C |
| D. 15 ngày | C |
| Câu 10: Mục tiêu chính của quy chữa là gì? | |
| B. Đảm bảo chất lượng & xử lý lỗi | A |
| A. Tăng doanh thu | A |
| tồn kho | A |
| chế sản xuất pin mới | A |