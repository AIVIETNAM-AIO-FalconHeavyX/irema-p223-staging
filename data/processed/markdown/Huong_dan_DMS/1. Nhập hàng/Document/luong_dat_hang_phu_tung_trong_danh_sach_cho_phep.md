---
document_id: HUON043
title: Luồng đặt hàng phụ tùng trong Danh sách cho phép
source_file: Luồng đặt hàng phụ tùng trong Danh sách cho phép.docx
source_path: Huong_dan_DMS/Luồng đặt hàng phụ tùng trong Danh sách cho phép.docx
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

# Luồng đặt hàng phụ tùng trong Danh sách cho phép

# Document Content

luồng đặt hàng theo Whitelist part/Danh sách phục tùng cho phép đặt

1. Đại lý/Showroom chỉ được phép đặt phụ tùng nằm trong Whitelist/Danh sách cho phép. Nếu cơ sở gán phụ tùng không được active whitelist, khi bấm lưu hệ thống Hệ thống hiển thị Pop-up thông báo “Mã sản phẩm: [XXXXX], [YYYYY]  không cung cấp, vui lòng kiểm tra lại”/ “These product codes like [XXXX],[YYYYY] is not supplied, please recheck” -> Cơ sở sẽ phải chọn X để xóa các line phụ tùng hệ thống cảnh báo thì mới có thể lưu chi tiết đơn hàng.

2. Với những đơn hàng đã gán phụ tùng trước khi lên luồng whitelist vẫn đang ở trạng thái mở, cơ sở chỉ có thể gửi khi tất cả phụ tùng đều active whitelist. Nếu trên đơn hàng cũ có ít nhất 1 mã không active whitelist hệ thống sẽ đưa ra cảnh báo: “Mã sản phẩm: [XXXXX], [YYYYY]  không cung cấp, vui lòng kiểm tra lại”/ “These product codes like [XXXX],[YYYYY] is not supplied, please recheck” -> Cơ sở cần phải xóa line phụ tùng đó ra khỏi đơn hàng mới có thể thao tác tiếp.

3. Để kiểm tra phụ tùng trong whitelist/Danh sách cho phép cơ sở vào Quản lý tồn kho -> Cài đặt -> Whitelist -> View active hiển thị các mã phụ tùng cơ sở được phép đặt hàng. Nếu mã cơ sở cần đặt không hiển thị ở đây vui lòng liên hệ Bộ phận cung ứng đơn hàng để kiểm tra.

4. Đặt hàng tự động (RNN): Chỉ chạy tự động đặt hàng đối với các Parts có config Min-Max và nằm trong whitelist.

5. Whitelist sẽ được SAP chạy đồng bộ hàng ngày lên DMS.

Theo như phòng phụ tùng hướng dẫn, nếu cơ sở có thắc mắc vì sao mã phụ tùng cần đặt không ở trong Whitelist/Danh sách cho phép, cơ sở có thể lên STP để kiểm tra nguyên nhân hoặc liên hệ Phòng phụ tùng.