<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Security policy

Copyright 2026 FreshMesh-DXOS contributors. This project is Apache-2.0 licensed.

## Reporting a vulnerability

Do not open a public issue for an undisclosed vulnerability. Use GitHub's private
security reporting page at <https://github.com/EngLandLee/FreshMesh-DXOS/security>.
Include impact, affected commit/version and reproduction steps using no real
personal data. Maintainers coordinate remediation and disclosure; this policy
does not promise an unverified response SLA.

If private contact is unavailable, open an issue containing only the words
"security contact requested" and no exploit details.

## Security boundaries

- Development credentials in `.env.example` are placeholders only. Rotate every
  local credential before exposing the stack.
- The portal uses OIDC Authorization Code + PKCE S256; browser password grants are
  prohibited. Direct access grants are a demo-only CLI convenience and are not a
  portal flow.
- The gateway is the only public application ingress. Database, object storage,
  workflow, and API administration ports stay on the Compose network.
- API authorization checks issuer, signature, audience, expiry, chain, store, role,
  and driver assignment. Never rely on UI-hidden controls.
- Document download requires an authenticated transfer participant with policy
  authorization. Filenames and content types are treated as untrusted input.
- Check stock and transition idempotency in the same durable transaction. Workflow
  retries use an operation identifier and must not apply a stock effect twice.
- Optional Ollama is not a trusted policy or authorization source and is disabled by
  default.

Run `make verify` before release and inspect `make release` SBOM output. Report newly
discovered vulnerable dependencies through the private channel above.
