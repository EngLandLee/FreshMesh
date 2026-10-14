<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Verification evidence — 2026-10-14

These are observed local runs, not an assertion that every deployment is production-safe
or that judges will award a particular score.

| Gate | Observed result |
|---|---|
| `make verify` | 13 regression tests passed; backend lint, portal JS syntax, Compose and source-license audit passed |
| `make demo-check` | Real four-core HTTP flow passed: transfer `810e51c6-3d4a-4430-baf4-aa46dcab8865`, 2 dispatched / 1 received, reservation/rejection, access denial, document hash, Flowable tasks and API-restart persistence |
| `make ui-check` | Chromium PKCE + four real actors passed: transfer `6c5fbd8e-ded0-419d-9bec-4dad1155b0f5`, route `24d2d199-5a82-4f28-b01d-c4575ee61a3b`, 4 dispatched / 3 delivered / 3 received, download integrity, mobile width 390 |
| Manual UI exercise | Same role-separated path, transfer `f8b6b4ba-583c-47f6-8264-4a1e0050ada5`; actual receipt upload and persisted timeline inspected |
| Visual verification | Desktop 1440 and mobile 390; four mandatory cores ready, hidden login panel absent after SSO and no horizontal page overflow |
| Optional AI | Gateway returned HTTP 200 from actual Ollama `qwen2.5:0.5b`; source provenance and model warning returned, no fabricated fallback. This does not establish answer quality or numerical correctness. |
| Clean-volume source startup | A separate `freshmesh-clean` project initialized new PostgreSQL/Keycloak/S3 volumes with no manual account repair; HTTP and patched-browser gates passed. HTTP transfer `23c1563b-3a96-423c-a3a7-87421aa14b47`; browser transfer `6dd5d577-6461-42de-91e7-313f4fe3c1a9`. |

## Repeatability

Run from source:

```sh
make up
make verify
make demo-check
npm ci --ignore-scripts
npx playwright install chromium
make ui-check
```

`make demo-check` and `make ui-check` intentionally create synthetic transfers and
consume source stock. They do not silently reset records or renew expiry dates.
Start a new isolated demo database if existing demo inventory has expired or been
consumed; do not delete business volumes without operator consent.

GitHub CI results are available at
https://github.com/EngLandLee/FreshMesh-DXOS/actions . The source release is generated
only after the repository is committed and its tracked worktree is clean; release
checksum and archive-content verification are separate from these runtime gates.
