<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Báo cáo cá nhân: FreshMesh-DXOS

## Góc nhìn và bài toán

Một cửa hàng dư hàng tươi cận hạn, cửa hàng khác thiếu hàng. Vấn đề không chỉ là
thuật toán tìm số lượng hoặc tuyến ngắn: ai được đề xuất, ai chịu trách nhiệm duyệt,
đã xuất bao nhiêu, tài xế giao bao nhiêu và cửa hàng thực nhận bao nhiêu phải được
kiểm chứng. FreshMesh chọn **P — Quy trình số** làm không gian HPDI chính.

Dự án là một nền tảng lõi tích hợp nguồn mở và một portal quy trình dùng lõi đó,
không phải một dashboard AI đơn lẻ. Không sử dụng IoT. Phân tách dữ liệu theo chuỗi;
điều chuyển chỉ giữa các cửa hàng trong cùng chuỗi, không chia sẻ tồn kho sang chuỗi khác.

## Điều chỉnh so với ý tưởng ban đầu

- Giữ bài toán hàng tươi, đề xuất nhập/giảm giá/điều chuyển, tối ưu thứ tự giao nhận
  và trợ lý tiếng Việt. Chỉ điều chuyển/giao nhận có đường thực thi nghiệp vụ;
  nhập hàng và giảm giá là khuyến nghị, chưa kết nối nhà cung cấp/POS.
- Dự báo ban đầu dùng trung bình bán 7 ngày, hiển thị công thức và giả định; không
  gọi đây là mô hình FL hay tuyên bố độ chính xác chưa đo.
- Không phát hành mã PACO hoặc mã analytics nguồn khác khi chưa có giấy phép.
  Solver tuyến dùng OR-Tools có license Apache-2.0.
- AI dùng Ollama + Qwen2.5-0.5B-Instruct (Apache-2.0), là tính năng bổ trợ, không
  thay người phê duyệt và không phải điều kiện để demo bốn lõi chạy được.

## Đối chiếu đề OLP

| Yêu cầu | Thành phần | Chứng minh trong demo |
|---|---|---|
| Identity/SSO | Keycloak, OIDC Authorization Code + PKCE | Đăng nhập các vai trò qua cùng nhà cung cấp danh tính |
| API Gateway | Apache APISIX | Portal chỉ gọi /api qua gateway, có request ID và giới hạn tốc độ |
| Dữ liệu cấu trúc/phi cấu trúc | PostgreSQL + SeaweedFS S3 | Tồn kho, phiếu, audit trong DB; tải chứng từ và đối chiếu SHA-256 |
| Workflow headless | Flowable OSS + BPMN | Duyệt/từ chối → điều phối → giao → nhận, kiểm tra task thật |
| Giao diện HPDI tầng 2 | Portal P | Hàng đợi việc, trạng thái, chứng từ, các thao tác theo vai trò |
| Bài toán nghiệp vụ | FreshMesh | Giữ hàng, trừ tồn nguồn, nhập tồn đích, ghi chênh lệch |

Bảy lớp công nghệ trong đề là kiến trúc tham chiếu; không nhận là đã triển khai
streaming, lakehouse, sổ cái mật mã hay IoT khi sản phẩm không có những phần đó.

## Phần mình viết và phần tích hợp

Mã gốc của dự án: portal HTML/CSS/JS; xác minh token và phân quyền API; mô hình dữ liệu;
quy tắc đề xuất; adapter tính tuyến; luồng giao nhận và chứng từ; adapter Flowable
Java; BPMN; cấu hình tích hợp; scripts, kiểm thử và tài liệu. Giấy phép Apache-2.0.

Sản phẩm tích hợp: Keycloak, APISIX, PostgreSQL, SeaweedFS, Flowable, OR-Tools,
nginx và tùy chọn Ollama. Không nhận các động cơ đó là mã tự viết. Giấy phép và
ranh giới phân phối được ghi trong [LICENSES/INVENTORY.md](../LICENSES/INVENTORY.md).

## Cách triển khai repo

- `backend/`: API headless, dữ liệu nghiệp vụ, phân quyền và quyết định.
- `workflow/`: adapter Java, BPMN và cấu hình nguồn để build.
- `portal/`: giao diện P, đăng nhập PKCE và thao tác thực tế.
- `deploy/`, `compose.yaml`: cấu hình kết nối bốn lõi và lưu trữ bền vững.
- `scripts/`, `.github/`: verification, E2E, license audit, SBOM và release.
- `LICENSE`, `NOTICE`, `CHANGELOG`, `CONTRIBUTING`, `SECURITY`, `docs/`: PoF và cộng đồng.

Lệnh kiểm chứng: `make up`, `make verify`, `make demo-check`.
Release chỉ chứa mã nguồn có giấy phép; không chứa cookie, khóa API, DB hay model weights.

## Luồng trình bày buổi đầu

1. Nêu dư–thiếu hàng và trách nhiệm giao nhận: vấn đề, người dùng, giới hạn.
2. Đối chiếu 3 tầng, 4 lõi, HPDI P; phân biệt với 7 lớp tham chiếu.
3. Mở repo, chỉ phần tự viết/tích hợp, license và cách dựng từ nguồn.
4. Demo quản lý nguồn tạo phiếu và chứng từ; chủ chuỗi duyệt, lập tuyến và điều phối;
   tài xế báo giao thiếu; quản lý đích xác nhận đúng số nhận.
5. Chứng minh tồn kho và chênh lệch thực sự thay đổi; truy cập trái quyền bị chặn.
6. Nêu giới hạn: dữ liệu demo, tuyến đường chim bay, AI có thể sai; không tuyên bố
   kết quả kinh doanh thật hoặc chắc chắn được 50 điểm.

Nguồn chuẩn: [đề thi](https://vfossa.vn/tin-tuc/de-thi-phan-mem-nguon-mo-olp-2026-798.html)
và [thể lệ](https://vfossa.vn/tin-tuc/the-le-olp-phan-mem-nguon-mo-nam-2026-760.html).
