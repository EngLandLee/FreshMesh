<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Third-party license inventory

This inventory records products required by the reference deployment. It is an
attribution and review index, not a relicensing notice. Exact dependency versions
are pinned by the manifests in each service; generated lock files and image SBOMs
are authoritative for a particular build.

| Product | Use in OLP | License / attribution source | Distribution boundary |
| --- | --- | --- | --- |
| PostgreSQL 16 | Relational persistence | PostgreSQL License, https://www.postgresql.org/about/licence/ | External container/runtime; not copied into this repository |
| Keycloak 26.0.7 | OIDC identity and JWT issuer | Apache License 2.0, https://www.keycloak.org/license | External container/runtime |
| Apache APISIX 3.11 | API gateway and rate limiting | Apache License 2.0, https://apisix.apache.org/license/ | External container/runtime |
| SeaweedFS 3.80 | S3-compatible object storage | Apache License 2.0, https://github.com/seaweedfs/seaweedfs/blob/master/LICENSE | External container/runtime |
| Flowable OSS 7.0.1 | BPMN workflow engine | Apache License 2.0, https://github.com/flowable/flowable-engine/blob/main/LICENSE.md | Workflow wrapper uses public APIs; engine is a build dependency |
| Python / FastAPI / Uvicorn | API service runtime | Python Software Foundation License / MIT, see upstream notices | Build/runtime dependencies, lock metadata and SBOM identify exact transitive versions |
| Psycopg 3 | Python PostgreSQL client | LGPL-3.0-or-later, https://github.com/psycopg/psycopg | Package-managed dependency; not relicensed as Apache-2.0 |
| PyJWT / cryptography / boto3 / httpx / Pydantic | JWT validation, S3 and API contracts | MIT / Apache-2.0 OR BSD-3-Clause / Apache-2.0 / BSD-3-Clause / MIT; inspect installed distribution metadata | Versioned in `backend/uv.lock`; external libraries, not copied source |
| Spring Boot 3.2.5 | Headless workflow adapter runtime | Apache-2.0, https://github.com/spring-projects/spring-boot | Maven-managed, versions inherited from its published BOM |
| Ollama / Qwen2.5-0.5B-Instruct | Optional local advisory AI | MIT / Apache-2.0, https://github.com/ollama/ollama and https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | External runtime/model download; no weights in source release |
| PostgreSQL JDBC driver | Workflow database connectivity | BSD-2-Clause, see upstream artifact metadata | Build dependency |
| OR-Tools | Route distance/order estimate where enabled | Apache License 2.0, https://developers.google.com/optimization/ | Build dependency; route output labels assumptions |
| Playwright Test 1.55.1 | Real-browser verification only | Apache-2.0, https://github.com/microsoft/playwright | npm-managed development dependency; browser binaries are downloaded, not bundled |
| nginx | Static portal and reverse proxy | 2-clause BSD, https://nginx.org/LICENSE | External container/runtime |
| Docker Compose | Local orchestration | Apache License 2.0, https://github.com/docker/compose/blob/main/LICENSE | Developer tool, not bundled |

## Optional model profile

A deployment MAY define an `ai` profile to run Ollama and a model selected by the
operator; this source release does not claim that profile exists in every deployment.
No model weights are included in source releases. Model cards and terms vary by model
and must be reviewed by the operator before `ollama pull`; the selected model's own
license and notices govern use. Core inventory, transfer, workflow, and receipt
features do not require this optional profile.

## Reviewing a build

Run `make release` after a clean checkout. It writes a source-only tarball,
`SHA256SUMS`, and `sbom.cdx.json` under `dist/`. The release SBOM records the
complete Python `uv.lock` set, direct workflow POM dependencies, and pinned Compose
images. It intentionally does not claim Maven-transitive or complete image coverage;
the CI Syft workflow scans source manifests, not complete runtime images or a guarantee of all Maven transitives.
