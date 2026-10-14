<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Contributing to FreshMesh-DXOS OLP

Copyright 2026 FreshMesh-DXOS contributors. This project is Apache-2.0 licensed;
see [LICENSE](LICENSE).

## Before changing code

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), the API contract, and the
security policy. Keep the source boundary explicit: do not copy code or data from
an unlicensed parent project, commit credentials, add binaries, or vendor runtime
images. New source files MUST carry an SPDX header and the 2026 FreshMesh-DXOS
copyright notice, for example:

```text
SPDX-License-Identifier: Apache-2.0
Copyright 2026 FreshMesh-DXOS contributors
```

Use the language's comment syntax. Documentation and configuration should include
the same notice where their format permits it.

## Development loop

1. Create a focused branch and explain the operational behavior being changed.
2. Copy `.env.example` to `.env`; never commit `.env`.
3. Start the real stack with `make up` and inspect `make logs` when debugging.
4. Run `make verify` and, for business-flow changes, `make demo-check`.
5. Keep migrations, API behavior, workflow transitions, UI permissions, and docs
   in sync. Error responses retain `{error:{code,message_vi}}`.
6. Submit a pull request using the template. Describe security impact, tests, and
   any license/dependency changes.

The coordinator owns public GitHub issues, release tags, and publication. Contributors
must not claim a release until the source-only archive, SHA256SUMS, and SBOM metadata
have been inspected.

## Review expectations

Reviews check tenant isolation, actor authorization, expiration/retry idempotency,
non-negative stock, durable audit events, and document access. Tests should exercise
both successful and denied paths. Avoid tautological checks that only assert a file
exists or that a process returns its input. Route output must disclose that distance
is estimated, and optional AI behavior must fail visibly when unavailable.

## Commit and pull request style

Use imperative, scoped subjects (for example, `Enforce receipt actor policy`). Keep
unrelated formatting out of a change. A maintainer may request a dependency license
entry, a changelog line, or a security note before merge.
