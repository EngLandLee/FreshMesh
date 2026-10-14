<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# Changelog

All notable changes to FreshMesh-DXOS OLP are recorded here. Dates use ISO 8601.

## [0.3.1] — 2026-10-14

### Fixed

- Enforced license metadata for every distributed tracked file, including arbitrary
  extensions and extensionless names; source archives use full-tree coverage.
- Added legal-text sidecars for LICENSE and NOTICE without modifying their text.
- Validated metadata sidecars and JSON/TOML lock syntax; kept ignored local environment
  credentials outside source coverage while rejecting credentials in source archives.
- Verified that an unknown-extension file fails without a header and passes with
  valid SPDX/copyright metadata. Public Pages was confirmed working after deployment.

## [0.3.0] — 2026-10-14

### Added

- Public landing page and original FreshMesh banner, also served at local `/about/`
  without moving the operational portal or changing OIDC callbacks.
- Real Playwright screenshot gallery across all portal sections, SSO, four-role
  transfer/route/delivery/receipt, evidence and mobile; optional actual agent capture.
- Source startup, screenshot reproduction and Git workflow guides; Linux devcontainer,
  editor configuration and line-ending conventions.
- PR evidence artifacts, trusted SemVer source-release automation and exact-source
  GitHub Pages deployment, with real Docker/HTTP/browser and static website gates.

### Changed

- Rebuilt README around project problem, capabilities, architecture, screenshots,
  setup and source ownership; removed the two requested promotional passages.
- Source-header audit now includes SVG artwork and editor/Git configuration.
- Corrected live-health and restart guidance; static verification is not service readiness.

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

[0.3.1]: https://github.com/EngLandLee/FreshMesh-DXOS/releases/tag/v0.3.1
[0.3.0]: https://github.com/EngLandLee/FreshMesh-DXOS/releases/tag/v0.3.0
[0.2.1]: https://github.com/EngLandLee/FreshMesh-DXOS/releases/tag/v0.2.1
[0.2.0]: https://github.com/EngLandLee/FreshMesh-DXOS/releases/tag/v0.2.0
