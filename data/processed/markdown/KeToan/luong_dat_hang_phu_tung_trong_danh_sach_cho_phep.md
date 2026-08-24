---
document_id: KETO758
title: Luồng đặt hàng phụ tùng trong Danh sách cho phép
source_file: Luồng đặt hàng phụ tùng trong Danh sách cho phép.docx
source_path: KeToan/Luồng đặt hàng phụ tùng trong Danh sách cho phép.docx
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

# Luồng đặt hàng phụ tùng trong Danh sách cho phép

**luồng theo Whitelist part/Danh sách

1. /Showroom chỉ được phép đặt phụ tùng nằm trong Whitelist/Danh sách . Nếu cơ sở gán phụ tùng không được active whitelist, hệ thống Hệ thống hiển thị Pop-up  “ **Mã sản phẩm: [XXXXX], [YYYYY]  , tra lại”/ “These product codes like [XXXX],[YYYYY] is not supplied, please recheck** ” -&gt; Cơ sở sẽ phải chọn X để xóa các line phụ tùng hệ thống cảnh báo thì mới có thể lưu chi tiết đơn hàng.

2. Với những đơn hàng đã gán phụ tùng whitelist vẫn đang ở trạng thái mở, cơ sở tùng đều active whitelist. Nếu trên cũ mã không active whitelist hệ thống sẽ đưa ra cảnh báo: “ **Mã sản phẩm: [XXXXX], [YYYYY]  , tra lại”/ “These product codes like [XXXX],[YYYYY] is not supplied, please recheck** ” -&gt; Cơ sở cần phải xóa line phụ tùng đó ra khỏi tiếp.


3. Để kiểm tra phụ tùng trong whitelist/Danh sách sở vào ** tồn kho -&gt; ; Whitelist -&gt; View active** hiển mã phụ tùng cơ sở được phép đặt hàng. Nếu mã cơ sở cần đặt không hiển ứng đơn hàng để kiểm tra.


4. Đặt hàng tự động (RNN): Chỉ chạy tự động đặt hàng đối với các Parts có config Min-Max và nằm trong whitelist.


5. Whitelist sẽ được SAP chạy đồng bộ hàng ngày lên DMS.

Theo như phòng phụ nếu cơ sở có thắc mã phụ tùng Whitelist/Danh sách , cơ sở có thể lên STP để kiểm tra nguyên nhân hoặc liên hệ Phòng phụ tùng.