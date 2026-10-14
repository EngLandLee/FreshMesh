# PoF delivery report

Copyright 2026 FreshMesh-DXOS contributors — SPDX-License-Identifier: Apache-2.0.

## Evidence map

| PoF requirement | Evidence |
| --- | --- |
| Original Apache-2.0 source boundary | `LICENSE`, `NOTICE`, headers, `LICENSES/INVENTORY.md` |
| Source quickstart and architecture distinctions | `README.md`, `docs/ARCHITECTURE.md` |
| Identity, tenant/store policy, workflow and stock effects | `docs/API.md`, `docs/DEMO.md`, backend/workflow contracts |
| Reproducible local orchestration | `Makefile`, `compose.yaml`, `.env.example` |
| Unit/static/license/compose verification | `Makefile`, `scripts/verify.sh`, `scripts/check-licenses.py` |
| Real integration acceptance | `scripts/demo-check.py`, `docs/DEMO.md` |
| Source-only delivery integrity | `scripts/release.sh`, `scripts/sbom.py`, `dist/SHA256SUMS`, CycloneDX metadata |
| Community and vulnerability handling | `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/` |

## Explicit limitations

- Route distance is an estimated haversine calculation, not live traffic or road routing.
- Recommendations are advisory and expose method, assumptions, provenance, and forecast
  inputs; they are not an autonomous decision-maker.
- Ollama/model use is optional and model licensing is operator responsibility.
- Demo credentials are development-only and must be rotated before deployment.
- The release archive contains source and metadata, not container images, binaries,
  runtime volumes, secrets, or model weights.
- The release SBOM covers the Python lock set, direct Maven POM dependencies, and pinned
  Compose images; CI Syft adds a source-manifest scan, not complete image/Maven-transitive coverage.
