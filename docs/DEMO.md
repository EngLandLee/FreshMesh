<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Demo vận hành 15 phút

Đây là luồng thật qua portal, không seed/fake HTTP response. Chuẩn bị từ source:

```sh
cp .env.example .env
make up
until curl --fail --silent http://localhost:3180/api/health; do sleep 3; done
```

Không dùng `make verify` làm dấu hiệu live health: lệnh đó không thay thế `curl` health
trực tiếp. Nếu cần log, chạy `make logs` ở terminal khác.

## 0–2 phút — đăng nhập và trust boundary

Mở `http://localhost:3180`, đăng nhập `manager_a1`/`demo123` qua Keycloak và chỉ ra
CHAIN_A/A-01. Portal dùng Authorization Code + PKCE S256; direct grant chỉ là tiện ích
CLI. Không chia sẻ mật khẩu demo ra ngoài môi trường cô lập.

## 2–5 phút — tồn và tạo yêu cầu

Ở Overview, ghi lại tồn source/destination. Với `manager_a1`, tạo một transfer
A-01 → A-02, số lượng **4**. Tạo thêm yêu cầu vượt tồn để quan sát từ chối. Tải lên một
file text nhỏ, tải xuống lại và đối chiếu SHA-256 trong chi tiết transfer.

## 5–8 phút — chính sách và tuyến

Đăng nhập lại `manager_a1`, thử duyệt để thấy authorization failure. Đăng nhập
`owner_a`, duyệt rồi lập tuyến cho `driver_a` và điều phối. Hiển thị process ID Flowable,
actor events và khoảng cách/thứ tự **ước tính OR-Tools** (một nguồn, một xe, giả định
được công bố; không phải định vị thời gian thực).

## 8–11 phút — giao và nhận

Đăng nhập `driver_a`, mở Delivery và ghi `actual_quantity=3` để thể hiện thiếu một đơn
vị. Đăng nhập `manager_a2`, nhận đúng 3. Mở timeline để xem submitted/approved/
dispatched/delivered/received và actor. Thử gửi lại transition: phải conflict/idempotent,
không nhân đôi tồn.

## 11–13 phút — cô lập và nhánh bị từ chối

Dùng token sai/hết hạn hoặc role không hợp lệ; gọi dữ liệu bằng `owner_b` (CHAIN_B) đối
với transfer CHAIN_A. Các request phải bị từ chối, không tiết lộ transfer/document.
Anonymous chỉ được xem config/health; tải tài liệu của tenant khác cũng bị chặn.

## 13–15 phút — bền vững và dọn dẹp

Ghi tồn trước/sau: source giảm theo xuất, destination tăng theo **3 thực nhận**.
Chạy `make down` rồi khởi động lại bằng `make up` (không xóa volume), chờ lại curl
health và mở transfer; state, tài liệu, timeline vẫn còn. Không chạy `docker compose down -v`
hoặc xóa named volume để reset. Tắt core bằng `make down` khi hoàn tất.

AI là tùy chọn; xem [OPTIONAL-AI](OPTIONAL-AI.md) nếu cần. Ảnh reproducible và mười
ba tên release xem [SCREENSHOTS](SCREENSHOTS.md); không gọi Public Pages là business
demo hosted.
