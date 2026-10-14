<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 FreshMesh-DXOS contributors -->
# LICENSES

See [INVENTORY.md](INVENTORY.md) for the product/dependency license inventory and
the boundary between FreshMesh source and externally obtained runtime images.

## Source-file coverage

The license audit's **ALL** scope means every distributed first-party source,
configuration, documentation, workflow, legal, and metadata file, including
extensionless and novel-extension names. Comment-capable files carry SPDX and
copyright in their first header. JSON/lock files and standardized legal text
keep their original syntax or upstream text and use a checked-in `.license`
sidecar instead. Sidecars are distributed metadata and are audited themselves.

Generated release outputs (`dist/`, including archives, checksums, SBOMs, and
screenshots/site images) plus dependency installs, caches, virtual environments,
runtime data, and secrets are not first-party source inputs and are excluded
from the source archive. The strict audit still rejects credential-like or
binary artifacts that appear in the distributable tree. This boundary does not
rewrite external dependencies or claim their authorship; see `INVENTORY.md` for
their attribution and licensing terms.
