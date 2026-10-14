<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Bản đồ trình diễn

Mở `http://localhost:3180`, đăng nhập `owner_a` với mật khẩu demo `demo123`,
rồi chọn **Lộ trình**. Bản đồ chạy cục bộ trong trình duyệt, không cần API key,
dịch vụ bản đồ hoặc tải nền bản đồ từ Internet.

1. Chọn **Tuyến minh họa · không lưu hệ thống** để trình diễn ngay.
2. Bấm **Chạy mô phỏng** để xem xe di chuyển qua các điểm dừng; có thể tạm dừng,
   đặt lại và đổi tốc độ trình diễn.
3. Chọn điểm dừng để xem thông tin; dùng các nút thu phóng hoặc **Vừa khung**.
4. Chọn một tuyến hệ thống để xem các điểm giao từ dữ liệu được cấp quyền.
   Việc xem và chạy mô phỏng không điều phối tuyến, không tạo phiếu và không
   thay đổi tồn kho. Điều phối vẫn dùng thao tác nghiệp vụ riêng.

Nền đường phố và sông là sơ đồ minh họa. Tuyến minh họa có các điểm được tạo
cho demo; tuyến hệ thống lấy vị trí được cấp quyền. Cả hai đều không phải
chỉ đường thực tế, GPS trực tiếp hay dự báo giờ đến. Tốc độ phát và phần trăm
tiến độ chỉ mô tả hoạt ảnh, không mô tả trạng thái giao hàng ngoài thực tế.

Kiểm tra trình duyệt chỉ đọc:

```sh
npm run test:map
```

Kiểm tra này xác nhận phát/tạm dừng/đặt lại, thu phóng, xem tuyến hiện có,
dừng khi rời trang, không ghi dữ liệu nghiệp vụ, và bố cục rộng 390px.
Ảnh chụp được lưu trong `dist/ui-redesign/`, ngoài mã nguồn phát hành.
Kiểm thử toàn bộ quy trình bốn vai trò vẫn dùng `make ui-check`; lệnh đó
tạo phiếu demo và tiêu thụ tồn kho demo.
