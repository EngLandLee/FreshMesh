<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# FreshMesh-DXOS OLP

[![Verification](https://github.com/EngLandLee/FreshMesh-DXOS/actions/workflows/unit.yml/badge.svg)](https://github.com/EngLandLee/FreshMesh-DXOS/actions/workflows/unit.yml)
[![License audit](https://github.com/EngLandLee/FreshMesh-DXOS/actions/workflows/license.yml/badge.svg)](https://github.com/EngLandLee/FreshMesh-DXOS/actions/workflows/license.yml)
[![Docker E2E](https://github.com/EngLandLee/FreshMesh-DXOS/actions/workflows/docker-e2e.yml/badge.svg)](https://github.com/EngLandLee/FreshMesh-DXOS/actions/workflows/docker-e2e.yml)

**FreshMesh-DXOS — điều chuyển hàng tươi có phê duyệt, lập tuyến và giao nhận thực tế.**
Xem [báo cáo cá nhân bằng tiếng Việt](docs/BAO-CAO-DAU-TIEN.md) và
[đối chiếu 50 điểm PoF](docs/POF-CHECKLIST.md).

FreshMesh-DXOS OLP is an original, Apache-2.0 licensed operations control plane for
multi-store inventory transfers. It provides auditable transfer approval, dispatch,
delivery, receipt, document evidence, stock effects, and route planning for a
multi-tenant chain. The primary HPDI axis is **P (process/workflow)**; data and
integration support it without turning the demo into an IoT system.

- Public repository: <https://github.com/EngLandLee/FreshMesh-DXOS>
- License: [Apache-2.0](LICENSE)
- Release notes: [CHANGELOG.md](CHANGELOG.md)
- Security reporting: [SECURITY.md](SECURITY.md)
- Contribution rules: [CONTRIBUTING.md](CONTRIBUTING.md)
- Published source, checksums and SBOM: [latest release](https://github.com/EngLandLee/FreshMesh-DXOS/releases/latest)
- Troubleshooting and report channels: [support](.github/SUPPORT.md)

**Navigate:** [What is included](#what-is-included) · [Architecture](#architecture-vocabulary) ·
[Source quickstart](#source-quickstart) · [Operational boundaries](#operational-boundaries) ·
[Documentation](#documentation-map) · [Community](#community-and-maintenance) · [License](#license)

## What is included

The source is independently authored FreshMesh-DXOS code. It does not distribute
source from an unlicensed parent analytics project. PostgreSQL, Keycloak, APISIX,
SeaweedFS, Flowable, nginx, and other external products are obtained under their
own licenses; see [LICENSES/INVENTORY.md](LICENSES/INVENTORY.md). Runtime data,
credentials, generated artifacts, binaries, and model weights are excluded from
source releases.

![Actual FreshMesh portal showing completed and rejected transfers](https://github.com/EngLandLee/FreshMesh-DXOS/releases/download/v0.2.1/portal-desktop.png)

Actual local browser capture, 2026-10-14, using synthetic demo data after Keycloak
PKCE login. It is not a mockup or evidence of a public production deployment.
The image and its Apache-2.0 notice are release assets, not bundled runtime binaries.

## Architecture vocabulary

The OLP follows the competition's exact three-tier reference architecture. These
tiers are not a list of containers:

| Tier | Contract | FreshMesh-DXOS mapping |
| --- | --- | --- |
| **T1 — headless** | Reusable Identity/SSO, API Gateway, structured and unstructured data, and Workflow services with no replacement UI | Keycloak, APISIX, PostgreSQL + SeaweedFS, and Flowable behind API contracts |
| **T2 — HPDI application** | At least one user-facing application in H, P, D, or I that consumes T1 | The P portal: approval tasks, evidence, status and accountable actions |
| **T3 — business domain** | Domain logic above the platform, not an additional mandatory app | FreshMesh transfer and route operations: stock, dispatch, delivery and receipt |

The primary HPDI space is **P (process/workflow)**. The portal uses the platform
for FreshMesh's specific workflow; this release does not claim an arbitrary
plugin marketplace or a generic no-code form builder.

The official seven functional reference areas are:

1. Experience and multi-channel interface
2. Network edge, gateway, and information security
3. Operations, logic, and entity state
4. Automation, process, and DevSecOps
5. Hyperconverged data, streaming, and ledger
6. Analytics, spatial services, and intelligence
7. Governance, search, and system observability

These seven areas are a reference architecture, not seven required services or a
claim that OLP implements every area. The four **mandatory T1 services** are
Identity/SSO, API Gateway, structured and unstructured data, and Workflow. The
optional AI integration is not one of the four.

The detailed sequence and trust boundaries are in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Source quickstart

Prerequisites: Docker Engine with Compose v2, `make`, `uv`, Python 3.12+, Node.js
22+, and a POSIX shell. Copy `.env.example` to `.env` and review every development
credential before starting:


```sh
cp .env.example .env
make up
# Portal: http://localhost:3180
make verify
make demo-check
```

Browser acceptance additionally needs `npm ci --ignore-scripts` and
`npx playwright install chromium`; then run `make ui-check`. CI installs these
from `package-lock.json`. Browser binaries are not bundled in source releases.

`make up` runs `docker compose up --build -d`. The portal proxies `/api` to the
APISIX gateway and `/auth` to Keycloak. The browser uses the configured public
client and PKCE; it never uses a password grant. Demo accounts and their explicit
local-only direct-access-grant caveat are documented in [docs/DEMO.md](docs/DEMO.md).

Useful lifecycle commands:

```sh
make down             # stop containers (keeps volumes)
make logs             # follow the stack
make verify           # tests, syntax, license/header audit, compose config
make demo-check       # real HTTP integration exercise; requires a running stack
make ui-check         # real Chromium UI: PKCE, four actors, delivery and documents
make release          # source-only archive, SHA256SUMS, and SBOM metadata in dist/
```

An optional `compose.ai.yaml` overlay runs actual Ollama with the Apache-2.0
Qwen2.5-0.5B-Instruct model: `make ai-up`. Weights stay outside the source release.
Missing or failed inference returns a visible error, not a prepared answer.
See [docs/OPTIONAL-AI.md](docs/OPTIONAL-AI.md).

## Operational boundaries

- Anonymous access is limited to `/api/config` and `/api/health`.
- JWT verification checks the Keycloak issuer, RS256 signature, audience, expiration,
  chain, and store claims. Cross-chain and cross-store attempts are denied.
- A transfer reserves source stock at creation, releases it on rejection, deducts it
  on dispatch, and increments destination stock on receipt. Receipt shortfall and
  the actor trail are persisted.
- Route distance is a deterministic haversine estimate, not live-road navigation.
  Recommendations state their method, assumptions, and provenance.
- Documents are streamed through authenticated API endpoints and identified by
  SHA-256; local credentials and runtime data are never release inputs.

## Documentation map

- [Architecture](docs/ARCHITECTURE.md) — trust boundaries, state changes, and limits
- [15-minute demo](docs/DEMO.md) — actor-by-actor acceptance path
- [Delivery report](docs/DELIVERY.md) — PoF evidence and known limitations
- [API contract](docs/API.md) — public request/response behavior and errors
- [Development](CONTRIBUTING.md) — source headers, tests, and review expectations

## Community and maintenance

- [Report a reproducible bug](https://github.com/EngLandLee/FreshMesh-DXOS/issues/new?template=bug_report.yml)
- [Correct documentation or dependency licensing](https://github.com/EngLandLee/FreshMesh-DXOS/issues/new?template=documentation.yml)
- [Propose an operational improvement](https://github.com/EngLandLee/FreshMesh-DXOS/issues/new?template=feature_request.yml)
- [Review ownership](.github/CODEOWNERS) — repository owner, not an invented team roster
- [Dependency updates](.github/dependabot.yml) — scheduled review PRs for Actions,
  npm, uv, Maven, Dockerfiles and Compose; no automatic merge
- [Code of conduct](CODE_OF_CONDUCT.md) and [private security reporting](SECURITY.md)

Every dependency change still requires license review and the applicable source
and runtime gates. A configured update schedule is not a claim that all images
are vulnerability-free or that an update PR has already run.

Repository-maintenance patterns were reviewed against
[HutechCJ/ProfioApp](https://github.com/HutechCJ/ProfioApp). Only missing support,
review ownership, dependency automation, issue routing and genuine screenshot
presentation were adapted; no code, logos or contributor claims were copied.

## License

Copyright 2026 FreshMesh-DXOS contributors. Licensed under the Apache License,
Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
