<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Đối chiếu 50 điểm PoF — không phải 50 điểm riêng GitHub

Nguồn: [thể lệ OLP PMNM 2026](https://vfossa.vn/tin-tuc/the-le-olp-phan-mem-nguon-mo-nam-2026-760.html).
Đây là bảng bằng chứng để giám khảo kiểm tra, **không phải cam kết được 50 điểm**.

| Tiêu chí chính thức | Điểm tối đa | Bằng chứng trong dự án |
|---|---:|---|
| Quản lý mã nguồn trên Internet và thực sự sử dụng | 5 | Repo công khai, Git history chia theo core/portal/PoF, issue #1 và #2 ghi acceptance và bằng chứng, milestone OLP |
| Giấy phép OSI, thông báo từng file, toàn văn và tương thích | 10 | Apache-2.0 `LICENSE`, `NOTICE`, SPDX/copyright trong mã, sidecar `.license` cho JSON/lock, `LICENSES/INVENTORY.md`, `scripts/check-licenses.py --strict` |
| Có bản phát hành theo phiên bản trước hạn nộp | 5 | Tag/release `v0.2.0`, source `.tar.gz`, release notes, SHA256SUMS; không dùng RAR/ZIP làm gói nộp chính |
| Hướng dẫn cấu hình, dựng và chạy từ nguồn | 10 | README, `.env.example`, Dockerfile backend/workflow/portal, `compose.yaml`, Makefile, `uv.lock`, Maven POM, CLI và Docker E2E CI |
| Thư viện/gói phụ thuộc rõ ràng, không copy/sửa thư viện ngoài | 10 | Package-managed Python/Maven, pin container versions, license inventory và SBOM; không phát hành mã PACO/analytics chưa có license |
| README, hướng dẫn, changelog và bug tracker | 10 | README, CHANGELOG, CONTRIBUTING, SECURITY, docs/API, docs/DEMO, báo cáo cá nhân và GitHub Issues/Templates |

## Những thứ giám khảo có thể tự kiểm chứng

```sh
make up
make verify
make demo-check
make release
sha256sum -c dist/SHA256SUMS
```

- `make verify`: regression về token sai chữ ký/issuer/audience/hết hạn/phạm vi;
  ràng buộc đề xuất, solver tuyến; lint; JavaScript syntax; Compose và license audit.
- `make demo-check`: các dịch vụ thật, không mock; đăng nhập; từ chối và giải phóng
  giữ hàng; chứng từ S3/hash; kiểm tra Flowable task qua từng bước; duyệt/lập tuyến/
  điều phối; giao thiếu/nhận; kiểm tra tồn kho chính xác; chặn truy cập trái quyền
  và thao tác nhận trùng; chứng từ và workflow vẫn tồn tại sau khi restart API.
- Portal: đăng nhập PKCE thật; quản lý nguồn tạo phiếu; chủ chuỗi duyệt và lập tuyến;
  tài xế giao; quản lý đích nhận; timeline và chênh lệch được lưu.
- AI là tùy chọn; `make ai-up` dùng Ollama + Qwen, không cần khóa dịch vụ đóng và
  không tham gia đường phê duyệt. Chất lượng văn bản chưa được đánh giá định lượng.

## Ranh giới cần nói rõ khi báo cáo

- Dữ liệu demo do dự án tự tạo, không phải doanh số thật; không công bố phần trăm
  giảm hao hụt hoặc tăng doanh thu chưa được đo.
- Hàng demo có hạn dùng tính khi tạo database đầu tiên. Restart giữ nguyên dữ liệu
  và hạn dùng; không tự gia hạn hoặc xóa dữ liệu để làm demo trông thành công.
- Khuyến nghị nhập hàng/giảm giá chưa thực thi với nhà cung cấp/POS. Luồng điều
  chuyển và giao nhận thực sự ghi tồn kho, không giả làm tích hợp hãng vận tải.
- Lộ trình tối ưu thứ tự điểm dừng bằng OR-Tools trên khoảng cách chim bay có quay
  về điểm gửi; không tuyên bố có đường phố thật, ETA hoặc giao thông thời gian thực.
- Source release không chứa binaries, weights, DB, `.env` thực hoặc cookie.
- Compose mặc định chỉ bind loopback, dùng tài khoản demo và Keycloak development;
  không tuyên bố là triển khai production công khai đã được harden.
- Source SBOM ghi Python lock, Maven trực tiếp và tag container; không tuyên bố là
  toàn bộ license/transitive inventory của mọi image hệ điều hành.

Repo: https://github.com/EngLandLee/FreshMesh-DXOS

Issue tracker: https://github.com/EngLandLee/FreshMesh-DXOS/issues

Release: https://github.com/EngLandLee/FreshMesh-DXOS/releases/tag/v0.2.0
