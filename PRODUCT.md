<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated by the user: original HTML/CSS/JavaScript portal, nginx, FastAPI,
PostgreSQL, Keycloak, APISIX, SeaweedFS and Flowable. Optional Ollama/Qwen.
No source from the unlicensed parent analytics/PACO project is distributed.

## Users

Small mini-mart chain operators handling perishable inventory. Source-store manager
proposes; chain owner approves and dispatches; assigned driver records delivery;
destination-store manager confirms actual receipt. These roles are an implementation
choice for the user's FreshMesh idea, not a claim about an existing customer.

## Product Purpose

An OLP 2026 DX-OS Open-Core demonstration focused on HPDI P. Four mandatory
headless services cooperate in a verifiable workflow, with actual inventory changes,
document evidence, actor accountability and tenant isolation. No IoT.

## Operating Context

Source-built local Compose deployment and a public source repository with PoF
licensing, dependencies, changelog, issue tracking, CI and source releases. Default
runtime is loopback-only with demo accounts; it is not a hardened public production
installation. The first report covers repo organization and the project's viewpoint.

## Capabilities and Constraints

- OIDC Authorization Code + PKCE S256; backend validates signed issuer/audience/scope.
- Reservation at creation, release on rejection, source deduction at dispatch,
  destination increment by actual receipt; no self-approval.
- Real Flowable BPMN tasks and durable S3 documents with SHA-256 verification.
- OR-Tools orders stops using estimated haversine distance; no live roads or IoT/GPS.
- Transparent seven-day-average forecasts and advisory purchase/markdown suggestions;
  these are not supplier/POS integrations or measured business improvements.
- Optional AI is read-only advisory inference, never an authorization/execution source.
- Synthetic seed data and measured E2E evidence; no real transaction dataset supplied.

## Brand Commitments

Name: FreshMesh-DXOS. Vietnamese operational copy. Technical, evidence-first language.
The user delegated implementation choices and explicitly excluded IoT.

## Evidence on Hand

`docs/VERIFICATION.md`, `scripts/demo-check.py`, `scripts/ui-smoke.mjs`, backend
regression tests, `docs/POF-CHECKLIST.md`, and the public GitHub issue/CI/release record.
No customer testimonials, real-business performance metrics or judge scores exist.

## Product Principles

1. Follow mandatory contest requirements; do not claim all seven reference layers.
2. Human accountability and server authorization outrank AI convenience.
3. Explain provenance and limitations rather than fabricate precision.
4. Source, licenses and verification must be reproducible and publicly inspectable.
