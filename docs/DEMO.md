# 15-minute operational demo

Copyright 2026 FreshMesh-DXOS contributors — SPDX-License-Identifier: Apache-2.0.

This run exercises the real stack. It does not seed fake HTTP responses. Prepare with
`cp .env.example .env && make up`; wait until `make verify` reports healthy services.
The deterministic automation is `make demo-check`, while these steps explain what an
operator should observe.

## 0–2 minutes — trust boundary

Open `http://localhost:3180`, sign in through Keycloak as `manager_a1` with the local
demo password from `.env.example`/realm setup, and show the chain/store identity. Explain
that the portal uses Authorization Code + PKCE and that direct access grants are a
CLI-only demo convenience, never a browser flow.

## 2–5 minutes — stock and request

On Overview, record source available stock and destination stock. As the manager,
create a transfer from A-01 to A-02. Show the submitted status and the reserved amount;
opening a second request beyond available stock must be denied. Upload a small text
document and download it again, checking the displayed SHA-256.

## 5–8 minutes — policy and workflow

Attempt approval as the requesting manager and show the authorization failure. Sign in
as `owner_a`, approve, and dispatch to an assigned driver. Show the Flowable process ID,
actor events, and the route's estimated-distance/assumption disclosure.

## 8–11 minutes — delivery and receipt

As the assigned driver, record a delivery (including an optional shortfall). As the
destination manager, receive the actual quantity. Show the immutable event trail and
that a repeated transition returns conflict/idempotent behavior instead of duplicating
stock.

## 11–13 minutes — isolation and failure paths

Use an invalid/expired token and an `owner_b` token against chain A. Both must be denied
without leaking transfer data. Show that unauthorized document download is denied and
that anonymous access remains limited to config/health.

## 13–15 minutes — durability and limits

Record before/after source and destination stock, restart the stack without removing
volumes, and reload the transfer. The state and audit trail remain. Explain that route
distance is haversine estimation, recommendations disclose assumptions/provenance, and
AI is optional; disabling Ollama does not break the core flow.
