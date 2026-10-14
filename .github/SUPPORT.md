<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# FreshMesh-DXOS support

## Start with the right guide

- [Source startup and prerequisites](../README.md#source-quickstart)
- [Role-separated transfer, route and delivery demo](../docs/DEMO.md)
- [API contracts and authorization errors](../docs/API.md)
- [Observed verification and repeatability](../docs/VERIFICATION.md)
- [Optional local AI and its limitations](../docs/OPTIONAL-AI.md)
- [Dependency licenses and provenance](../LICENSES/INVENTORY.md)

The default portal is `http://localhost:3180`, bound to the local machine. It is
not a hosted public demo. The provided accounts, data and passwords are only for
an isolated development demonstration, not production deployment.

## Diagnose without destroying data

1. Run `docker compose config --quiet` from the source root. Ensure `.env` exists
   locally and that Docker Engine with Compose v2 is available.
2. Run `docker compose ps` and inspect the affected service with
   `docker compose logs --tail=100 SERVICE`. The four-core health view is available
   in the portal and at `GET /api/health` through port 3180.
3. For invalid issuer or callback problems, compare the portal origin and Keycloak
   URLs with `.env.example`; do not disable signature, audience or tenant checks.
4. A transfer quantity conflict can mean insufficient available stock, an expired
   lot, or an already completed action. Demo checks deliberately consume stock.
   Do not reset a business database or delete its volumes to hide the problem.
5. Optional AI needs its separate overlay and model download. Main transfer and
   delivery actions do not require AI. Read the AI guide instead of replacing an
   inference error with a fabricated answer.

Review logs before sharing: remove cookies, bearer tokens, passwords, object-store
keys, personal data and private documents. Do not attach `.env` or raw browser
storage. Share the release tag, operating system, relevant command, redacted error,
actor role, reproducible steps and expected versus actual behavior.

## Choose a reporting channel

- [Bug report](https://github.com/EngLandLee/FreshMesh-DXOS/issues/new?template=bug_report.yml): reproducible runtime or source-build failure.
- [Documentation or license correction](https://github.com/EngLandLee/FreshMesh-DXOS/issues/new?template=documentation.yml): an incorrect command, missing dependency notice or unclear demo step.
- [Feature request](https://github.com/EngLandLee/FreshMesh-DXOS/issues/new?template=feature_request.yml): a justified operational improvement within the documented scope.
- [Private security report](https://github.com/EngLandLee/FreshMesh-DXOS/security/advisories/new): an exploitable vulnerability. Follow [SECURITY.md](../SECURITY.md); do not open a public issue with exploit details.

Reports and fixes are tracked publicly unless they are security-sensitive. This
student project does not promise commercial support or a response-time SLA.
