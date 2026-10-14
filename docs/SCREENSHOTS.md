<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Ảnh chụp luồng v0.3.0

Các liên kết dưới đây trỏ tới artifact release v0.3.0. Chúng mô tả trạng thái quan sát
được trong luồng demo, không phải ảnh mock hay cam kết số liệu sản phẩm. Có thể tái tạo
bộ ảnh bằng browser smoke thật:

```sh
cp .env.example .env
make up
until curl --fail --silent http://localhost:3180/api/health; do sleep 3; done
make screenshots
```

Lệnh tạo 13 ảnh trong `dist/screenshots/` và metadata/license cạnh ảnh; cần browser
Playwright và toàn stack chạy được. Không khẳng định một run mới đã pass nếu chưa có
bằng chứng runtime từ maintainer.

| Ảnh | Vai trò / trạng thái quan sát | Mục đích |
|---|---|---|
| [01-sso.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/01-sso.png) | `manager_a1`, màn hình SSO Keycloak | Thể hiện luồng Authorization Code + PKCE trước portal. |
| [02-overview.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/02-overview.png) | quản lý A-01, Overview | Tồn source/destination và transfer view ban đầu. |
| [03-recommendations.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/03-recommendations.png) | quản lý, khuyến nghị | Hiển thị recommendation cùng provenance/assumptions. |
| [04-create-transfer.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/04-create-transfer.png) | `manager_a1`, form tạo | Một request A-01 → A-02, 4 đơn vị, xe hàng duy nhất. |
| [05-submitted.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/05-submitted.png) | quản lý, submitted | Xác nhận phiếu đã gửi và lượng giữ chỗ. |
| [06-approval.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/06-approval.png) | `owner_a`, approval | Chủ chuỗi duyệt sau khi manager bị chặn quyền duyệt. |
| [07-route-form.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/07-route-form.png) | `owner_a`, route form | Chọn `driver_a`; đầu vào tuyến một xe. |
| [08-route-planned.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/08-route-planned.png) | owner, route planned | Khoảng cách/thứ tự OR-Tools ước tính và giả định. |
| [09-driver-delivery.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/09-driver-delivery.png) | `driver_a`, delivery | Tài xế ghi giao thực tế 3/4 (shortfall). |
| [10-store-receipt.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/10-store-receipt.png) | `manager_a2`, receipt | Cửa hàng đích chuẩn bị nhận lượng thực tế. |
| [11-receipt-evidence.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/11-receipt-evidence.png) | manager đích, evidence | Nhận 3, xem tài liệu, SHA-256 và timeline actor. |
| [12-core-health.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/12-core-health.png) | operator, health | Health của các service lõi sau startup. |
| [13-mobile.png](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.3.0/13-mobile.png) | giao diện viewport 390px | Kiểm tra portal responsive ở màn hình hẹp. |

Ảnh `14-optional-agent.png` chỉ là output local tùy chọn khi chạy với AI/Ollama
(`CHECK_AI=1` nếu script hỗ trợ); không có link release hoặc tuyên bố đã xác nhận.
