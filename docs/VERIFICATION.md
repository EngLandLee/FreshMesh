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

## Public source-release verification

The v0.2.0 source archive and checksum were downloaded from the published GitHub
release into a separate `/tmp/freshmesh-release-validation` directory. From that
directory, `sha256sum -c dist/SHA256SUMS` returned `OK`. After extraction, running
`make verify` from the archived source passed all 13 regression tests, backend lint,
JavaScript syntax, Compose validation and the 67-file source-license audit.
This is verification of a downloaded release, not only the working checkout.

The README portal image was captured from the running application after actual
Keycloak PKCE authentication as the demo chain owner. It shows synthetic completed
and rejected transfers from the already exercised HTTP/browser flows. No browser
tokens, cookies, credentials or production data are included in the image.

## v0.3.0 showcase verification

- Real Playwright gallery: transfer `1a684359-d747-42e1-ac25-cdd1467c4fdd`,
  route `40f911a8-f410-4a59-aa6b-bcc23ba1d1db`; four roles, 4 dispatched / 3 delivered /
  3 received, document download SHA-256, no runtime errors, 390px no overflow.
  Thirteen captures and their provenance ledger were generated without HTTP mocks.
- `make site-check` passed for desktop 1440 and mobile 390: all referenced images
  loaded, startup anchor navigation worked, document width stayed within viewport,
  and the original SVG banner was rendered to PNG. A real mobile grid-overflow
  defect was reproduced before the `min-width: 0` correction.
- `npm run test:map` passed: play/pause/reset, zoom/fit, saved authorized route,
  hidden-view pause, missing-origin/hostile-label boundaries, zero business writes,
  no runtime errors and 390px width. Existing user map/design work was preserved.
- The development image built with Dev Containers CLI 0.83.0; `up` completed and
  `exec` observed Python 3.12.15, Node 22.14.0, uv 0.11.1, JDK 21, Maven, Docker CLI/
  Compose and the actual host four-core health endpoint. A stale upstream Yarn key
  blocked the first base image; the source now uses a clean Python/Debian base,
  without disabling package signatures.
- Optional AI was exercised through actual SSO and gateway, returning HTTP 200
  from Ollama `qwen2.5:0.5b`. Gateway/portal deadlines now encompass the backend's
  120-second inference limit. This establishes connectivity, not numerical quality:
  observed generated wording can be wrong and is explicitly advisory.
- GitHub main protection was enabled with strict `unit`, `audit`, `e2e` checks,
  administrator enforcement, conversation resolution, no force pushes or deletion.
  This does not claim a human approval review. Pages accepts main and `v*` tags.

