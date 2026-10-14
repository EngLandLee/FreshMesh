<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Contributing to FreshMesh-DXOS OLP

Copyright 2026 FreshMesh-DXOS contributors. This project is Apache-2.0 licensed;
see [LICENSE](LICENSE).

## Trước khi thay đổi

Đọc [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), contract API, hướng dẫn
[bắt đầu](docs/GETTING-STARTED.md), [demo](docs/DEMO.md) và chính sách bảo mật.
Giữ ranh giới source rõ ràng: không sao chép code/dữ liệu từ dự án cha không có
giấy phép, không commit credential, binary, ảnh mock hoặc vendor runtime image.
Không đưa branding, danh sách contributor, sponsor hay số liệu không có bằng chứng
vào source/documentation.

Mọi source/config/docs/assets mới phải có SPDX Apache-2.0 và thông báo bản quyền
2026 FreshMesh-DXOS contributors theo định dạng phù hợp. JSON phải có file
`.license` cạnh file. Không commit `.env`; bắt đầu bằng:

```sh
cp .env.example .env
make up
until curl --fail --silent http://localhost:3180/api/health; do sleep 3; done
```

Source build bằng Make/Compose là authoritative; devcontainer chỉ là container
tooling Debian Python 3.12/Node 22 có Docker CLI + Compose qua Docker socket của
host. Socket cần quyền phù hợp và tương đương quyền root; không dùng daemon lồng
nhau. Không yêu cầu cloud/Gitpod/VS Code commercial service. Cổng portal là
`http://localhost:3180`; khi chạy container từ xa phải forward cổng về host.

## Vòng lặp phát triển

1. Tạo branch tập trung, mô tả hành vi vận hành thay đổi và tác động tenant/security.
2. Chạy stack thật bằng `make up`; kiểm tra **trực tiếp** `curl /api/health` cho tới
   khi database, identity, storage, workflow, gateway đều sẵn sàng. `make verify`
   không tự báo live health.
3. Dùng `make logs` để debug. Với thay đổi business-flow, chạy `make demo-check`;
   với UI/ảnh, chạy `make screenshots` và ghi rõ bằng chứng run.
4. Giữ migration, API, workflow transition, UI permission và docs đồng bộ. Error
   responses giữ `{error:{code,message_vi}}`.
5. Tạo PR với mô tả, checks đã chạy, security impact, dependency/license thay đổi.

Dừng bằng `make down` (giữ volumes). Không chạy `docker compose down -v` hay xóa
volume để né lỗi/trạng thái; dữ liệu và audit phải được kiểm tra trước mọi reset.

## Review và tài sản

Review kiểm tra tenant isolation, authorization theo actor, expiry/retry idempotency,
stock không âm, audit bền vững, document access và nhánh denied. Route phải nêu rõ
distance là estimate cùng assumptions; AI optional phải lỗi rõ ràng khi unavailable.
Ảnh/asset phải do project tạo hoặc có license ghi trong `LICENSES/INVENTORY.md`;
không copy ProfioApp hay branding/roster bên ngoài. Không tuyên bố release/benchmark
khi chưa có artifact và bằng chứng tương ứng.

## Commit và pull request

Dùng subject mệnh lệnh, có scope khi hữu ích (ví dụ `Enforce receipt actor policy`);
giữ diff nhỏ, không format lại phần không liên quan. PR phải nêu:

- vấn đề và cách thay đổi end-to-end;
- lệnh kiểm tra đã thực sự chạy (không ghi “passed” nếu chưa có evidence);
- ảnh/UI trước-sau nếu có, cùng nguồn/license asset;
- migration, backward-compatibility, security và dependency/license impact.

Maintainer có thể yêu cầu changelog, security note hoặc dependency inventory trước
merge. Không tự tag/release hoặc công bố archive/SBOM; coordinator sở hữu publication.

## Ownership và dependency maintenance

[CODEOWNERS](.github/CODEOWNERS) yêu cầu review từ repository owner; không khẳng định
branch protection hoặc human review đã xảy ra. Dùng issue forms hiện có; đọc
[support guidance](.github/SUPPORT.md) trước khi chia sẻ log. Vulnerability gửi qua
[SECURITY.md](SECURITY.md), không public issue.

[Dependabot](.github/dependabot.yml) lập lịch bounded update cho package manager đang
dùng; không có auto-merge. Review license và behavior upstream, cập nhật lock và
`LICENSES/INVENTORY.md` khi cần. Chạy `make verify` cho mọi thay đổi; thay đổi
runtime/container/workflow cần thêm Docker/browser gates theo hướng dẫn maintainer.

