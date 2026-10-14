<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Bắt đầu với FreshMesh-DXOS

Hướng dẫn này chạy **source và Docker Compose thật** trên Linux. Public Pages chỉ là
trang giới thiệu tĩnh; demo chạy tại `http://localhost:3180`.

## Điều kiện tiên quyết

- Linux/macOS/Windows với Docker Engine và Docker Compose v2 (`docker compose version`).
- `git`, `curl`, `make`, trình duyệt hiện đại. Docker phải đang chạy và tài khoản của
  bạn có quyền dùng Docker socket (thường thuộc nhóm `docker`; đăng nhập lại sau khi
  đổi nhóm). Quyền socket tương đương quyền root trên máy chủ, vì vậy chỉ dùng với
  máy tin cậy.
- Khi dùng devcontainer, container cần thấy Docker socket của host. Socket là kênh
  điều khiển Docker **ngoài** container, không phải Docker daemon lồng nhau; không
  khởi động daemon thứ hai. Cấu hình này dùng host networking trên Linux để CLI
  trong container truy cập đúng `localhost:3180` và issuer OIDC; quyền mạng/socket
  rộng, chỉ dùng trên máy tin cậy. Docker Desktop cần bật host networking tương
  ứng; nếu không hỗ trợ, dùng Make/Compose trực tiếp trên host thay vì đổi issuer.
- Các image/build dependency được tải từ Internet. Không cần tài khoản cloud,
  Gitpod hay dịch vụ VS Code thương mại.

## Cài đặt và khởi động

```sh
git clone https://github.com/EngLandLee/FreshMesh-DXOS.git
cd FreshMesh-DXOS
git checkout v0.3.0                 # hoặc commit/nhánh bạn muốn thử
cp .env.example .env                 # không commit file này
make up
```

`make up` build API FastAPI, workflow Java, và portal; Compose khởi động PostgreSQL,
Keycloak, SeaweedFS, APISIX và các service phụ thuộc. Lệnh có thể mất vài phút ở lần
đầu. Không coi `docker compose ps` hoặc `make verify` là bằng chứng endpoint đã sẵn
sàng: `make verify` là kiểm tra tĩnh/runtime nội bộ, không thay thế kiểm tra health
trực tiếp.

Chờ đến khi **tất cả** service health trả về `true`:

```sh
until curl --fail --silent http://localhost:3180/api/health; do sleep 3; done
curl --fail --silent http://localhost:3180/api/health
```

JSON phải có `status: "ok"` và các mục `database`, `identity`, `storage`, `workflow`,
`gateway` đều là true/healthy. Nếu chưa đạt, xem `make logs` hoặc
`docker compose ps`; không tiếp tục demo khi health chưa đủ.

Mở `http://localhost:3180` trong trình duyệt. Source build và Make/Compose ở trên là
đường chạy chính; trình duyệt chỉ là client, không cung cấp backend.

## Tài khoản demo và phạm vi

Realm local tạo các tài khoản sau, cùng mật khẩu `demo123` (chỉ dùng trong demo cô lập):

| Tài khoản | Vai trò | Phạm vi |
|---|---|---|
| `manager_a1` | quản lý cửa hàng | CHAIN_A / A-01, tạo phiếu |
| `owner_a` | chủ chuỗi | CHAIN_A, duyệt và lập/điều phối tuyến |
| `driver_a` | tài xế | CHAIN_A, chỉ phiếu được phân công |
| `manager_a2` | quản lý cửa hàng | CHAIN_A / A-02, xác nhận nhận |
| `owner_b` | chủ chuỗi khác | CHAIN_B, dùng kiểm tra cô lập; không thấy CHAIN_A |

Portal dùng Authorization Code + PKCE S256. Direct grant chỉ dành cho smoke/demo CLI,
không phải luồng đăng nhập trình duyệt.

## Luồng nghiệp vụ có thể quan sát

1. `manager_a1` tạo **một** phiếu A-01 → A-02 với **4 đơn vị** của một xe hàng.
   Tồn khả dụng được giữ chỗ; tạo vượt tồn bị từ chối.
2. `owner_a` duyệt, lập tuyến cho `driver_a`, rồi điều phối. Khoảng cách/thứ tự là
   ước tính OR-Tools (một nguồn, một xe), có hiển thị giả định; không phải GPS/live ETA.
3. `driver_a` ghi giao thực tế **3/4** (shortfall một đơn vị). `manager_a2` nhận 3.
   Tồn nguồn giảm theo lượng xuất/điều phối và tồn đích tăng đúng lượng thực nhận;
   sự kiện/timeline ghi actor và trạng thái. Lặp transition bị conflict/idempotent,
   không nhân đôi tồn.
4. Tải tài liệu chứng cứ, tải lại và đối chiếu SHA-256; lịch sử giữ timeline sự kiện.
   Token sai/hết hạn, role sai hoặc CHAIN_B gọi dữ liệu CHAIN_A đều bị từ chối, không
   làm lộ transfer/document khác tenant.

Chạy kiểm tra tự động sau khi health đạt:

```sh
make verify
make demo-check
```

`make verify` không tự báo live health của toàn stack; endpoint health ở trên là bắt
buộc. `make demo-check` thực hiện luồng API thật và kiểm tra các nhánh được phép/từ
chối. UI/browser flow và ảnh reproducible được mô tả trong [DEMO](DEMO.md) và
[SCREENSHOTS](SCREENSHOTS.md).

## AI tùy chọn

Luồng lõi không cần AI. Chỉ khi muốn tải model local:

```sh
make ai-up
```

Lệnh chạy overlay Ollama và tải `qwen2.5:0.5b`; model/weights không nằm trong source
release, cần kiểm tra model card, license, điều khoản sử dụng và dung lượng trước khi
tải. AI chỉ advisory, không cấp quyền, không thay đổi tồn. Khi Ollama không sẵn sàng,
API trả lỗi 503 có cấu trúc; tắt AI không làm hỏng luồng lõi. Quay lại core-only bằng
`make up`.

## Dừng an toàn, dữ liệu và reset

```sh
make down                         # dừng/xóa container, giữ named volumes
make up                           # dựng lại container, sử dụng volumes đã giữ
```

Không dùng `docker compose down -v`, `docker volume rm`, hay xóa volume để “reset”
trong khi điều tra: PostgreSQL, Keycloak và SeaweedFS chứa trạng thái/audit/tài liệu.
Muốn môi trường demo hoàn toàn mới, chỉ thực hiện việc xóa volume sau khi đã xác nhận
đó là dữ liệu disposable và được người sở hữu môi trường cho phép. Không đòi hỏi reset
để chạy lại; các transition hợp lệ phải idempotent.

## Sự cố thường gặp

- **Health chưa đủ:** `docker compose ps`, `make logs`; chờ image migration/build hoàn
  tất, sau đó lặp `curl --fail http://localhost:3180/api/health`.
- **Không vào được 3180:** kiểm tra port đã bị chiếm (`ss -ltnp | grep 3180`), Docker
  đang chạy và portal đã healthy. Trong devcontainer, forward port từ host/container
  đúng cách; không truy cập `localhost` của container khác.
- **Keycloak redirect/401:** giữ nguyên các URL trong `.env.example`, dùng đúng
  `http://localhost:3180`; không tắt kiểm tra issuer/signature/tenant.
- **Docker permission denied:** thêm user vào nhóm Docker hoặc dùng socket policy do
  quản trị viên cấp; không chạy image lạ bằng socket root một cách mù quáng.
- **Demo thiếu tồn hoặc trạng thái cũ:** đừng xóa volume. Ghi nhận trạng thái hiện
  tại, kiểm tra timeline và dùng một transfer hợp lệ khác; dữ liệu Compose là bền vững.
- **AI 503:** bình thường khi chưa chạy `make ai-up`; tiếp tục core flow hoặc xem
  [OPTIONAL-AI](OPTIONAL-AI.md).
