<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Changelog

All notable changes to FreshMesh-DXOS OLP are recorded here. Dates use ISO 8601.

## [0.2.1] — 2026-10-14

### Repository maintenance

- Added owner review routing, bounded Dependabot schedules for the existing package
  managers, and support guidance without introducing hosted or proprietary requirements.
- Added a documentation/license issue form and private-security report navigation.
- Improved README navigation, real Docker E2E badge and an actual authenticated portal
  screenshot distributed as a separately licensed release asset.
- Adapted only missing repository-presentation patterns from HutechCJ/ProfioApp;
  no third-party source, branding, contributor roster or badge claims were copied.
- Documented verification of the publicly downloaded v0.2.0 source archive.

### Fixed

- Granted release-asset write permission only to the SBOM job after the real
  v0.2.0 release exposed an attachment permission failure; removed duplicate
  artifact upload. Source scanning itself had succeeded.

## [0.2.0] — 2026-10-14

### Added

- Original Apache-2.0 FreshMesh-DXOS OLP source boundary and attribution inventory.
- Three logical DX-OS tiers: headless foundation, HPDI P portal and FreshMesh business domain.
- Transfer lifecycle with tenant/store authorization, document receipts, route planning,
  stock reservation/deduction, and audit events.
- Reproducible Compose startup, verification, demo-check, source-only release, checksums,
  and CycloneDX metadata interfaces.
- Optional Ollama profile explicitly separated from the core operational workflow.

### Documentation

- Added contributor, security, conduct, architecture, demo, and delivery guidance.

[0.2.1]: https://github.com/EngLandLee/FreshMesh-DXOS/releases/tag/v0.2.1
[0.2.0]: https://github.com/EngLandLee/FreshMesh-DXOS/releases/tag/v0.2.0
