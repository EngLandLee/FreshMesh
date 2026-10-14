# API contract

Copyright 2026 FreshMesh-DXOS contributors — SPDX-License-Identifier: Apache-2.0.

The external base is `http://localhost:3180/api`; production deployments MUST use
TLS. Business endpoints require a Keycloak RS256 bearer token with audience
`freshmesh-api`. Errors use `{ "error": { "code": "...", "message_vi": "..." } }`.

## Anonymous endpoints

- `GET /config` returns issuer, `client_id` (`freshmesh-portal`), name, version, and
  `hpdi: "P"`.
- `GET /health` returns status and booleans for database, identity, storage, workflow.

## Identity and read models

- `GET /me` returns username, user ID, role, chain, and store claim.
- `GET /overview` returns permitted stores, lot stock (`quantity`, `reserved`,
  `available`, expiry, cost), and transfer counts.
- `GET /recommendations` returns transfer/markdown/purchase items with method,
  assumptions, provenance, and estimated value.
- `GET /drivers` returns drivers visible to the caller's chain.
- `GET /transfers` returns only policy-visible transfers and their event/doc summaries.

## Transfer and evidence commands

`POST /transfers` accepts `source_store_id`, `target_store_id`, `lot_id`, `quantity`,
and optional `note`; it reserves stock and returns a submitted transfer. Commands are:

- `POST /transfers/{id}/approve` with `decision` (`approved` or `rejected`) and note.
- `POST /transfers/{id}/dispatch` with `driver_username`.
- `POST /transfers/{id}/deliver` with `actual_quantity` and note.
- `POST /transfers/{id}/receive` with `actual_quantity` and note.
- `POST /transfers/{id}/documents` multipart upload; response includes ID, filename,
  size, and SHA-256.
- `GET /transfers/{id}/documents/{document_id}` streams authenticated bytes.

Each transition is authorization-checked, persisted with actor/time/note, and conflict
safe. The API coordinates Flowable; clients do not complete BPMN tasks directly.

## Routes and AI

`GET /routes` lists visible routes. `POST /routes` accepts transfer IDs and a driver;
`POST /routes/{id}/dispatch` executes dispatch for eligible transfers and reports
partial failures instead of claiming all succeeded. Route responses disclose estimated
haversine distance and assumptions. `POST /agent/chat` calls configured Ollama only;
when unavailable it returns 503 and the UI states that AI is not available.
