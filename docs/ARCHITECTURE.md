# Architecture and boundaries

Copyright 2026 FreshMesh-DXOS contributors — SPDX-License-Identifier: Apache-2.0.

## Three-tier reference architecture

The OLP keeps the competition's three tiers distinct from deployment containers:

1. **T1 — headless foundation:** reusable Identity/SSO, API Gateway, structured and
   unstructured data, and Workflow services. Keycloak, APISIX, PostgreSQL +
   SeaweedFS, and Flowable provide these contracts without replacing the T2 UI.
2. **T2 — HPDI application:** at least one user-facing H/P/D/I application consuming
   T1. FreshMesh's primary space is **P (process/workflow)**; its portal handles
   approval tasks, evidence, status and accountable actions for the FreshMesh workflow.
3. **T3 — business domain:** transfer and route logic supplies stock, dispatch,
   delivery and receipt behavior. No arbitrary plugin marketplace is implemented.

The seven functional reference areas are:

1. Experience and multi-channel interface
2. Network edge, gateway, and information security
3. Operations, logic, and entity state
4. Automation, process, and DevSecOps
5. Hyperconverged data, streaming, and ledger
6. Analytics, spatial services, and intelligence
7. Governance, search, and system observability

They are reference areas, not seven required services or a claim that this slice
implements every area. The four mandatory T1 services are Identity/SSO, API Gateway,
structured and unstructured data, and Workflow.

## Runtime boundaries

The portal is served by nginx. The browser obtains tokens from Keycloak through
`/auth`, then calls same-origin APISIX `/api`; it stores no service credentials and
uses Authorization Code + PKCE S256. APISIX adds request IDs and rate limits. The
FastAPI API verifies RS256 issuer, audience, expiry, and tenant/store claims. The
Flowable wrapper owns BPMN process state and idempotent operation IDs; the browser
never completes BPMN tasks directly.

PostgreSQL stores domain state, audit events, transfer/route records, and workflow
persistence. SeaweedFS stores authenticated document bytes. Optional Ollama is
outside the four mandatory services and isolated from authorization. Only the portal
and Keycloak login proxy are intended for host access; database, storage, workflow,
and API administration surfaces remain internal to Compose.

## Transfer lifecycle

1. A store manager submits a transfer within their chain/store policy. The API locks
   the source lot and reserves quantity transactionally.
2. The owner approves or rejects. Approval cannot be performed by the requester;
   rejection releases the reservation.
3. An owner dispatches to an assigned driver. Dispatch deducts reserved source stock
   and records a durable event.
4. The driver records delivered quantity and may report a shortfall. The destination
   manager receives the shipment; receipt increments destination stock by actual
   received quantity and records the actor trail.
5. Every transition carries an operation ID into Flowable. Retrying exactly the same
   decision, actor and evidence after a timeout is idempotent. A changed decision
   is not a retry and must not overwrite a completed workflow task. Duplicate
   committed state transitions return a conflict.

The DB transaction and Flowable transaction are separate. A process may be ahead
after a network timeout or commit failure; stable operation IDs and task
acknowledgement checks allow retrying the same action without double stock effects.
This is not a cross-service distributed transaction or a claim of exactly-once
delivery across arbitrary failures. An orphan workflow can exist if transfer
creation starts a process but its local DB transaction fails.

## Security and tenancy

Roles are owner, store_manager, and driver. Chain and store claims are enforced in
backend policy for every business endpoint; a hidden UI control is not security.
Owners are chain-scoped, managers are store-scoped, and drivers are assignment-scoped.
Cross-chain, cross-store, unassigned-driver, invalid-token, expired-token, and missing
claim requests return a structured error and never reveal another tenant's data.


## Route and recommendation limits

Route plans use deterministic haversine distance and disclose that it is an estimate,
not live-road navigation. Recommendation responses include method, assumptions,
provenance, and forecast inputs. They are advisory and cannot approve, dispatch, or
receive a transfer.
