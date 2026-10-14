#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
set -eu

repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo"

# A release must describe exactly committed source; dirty trees can contain secrets
# or unreviewed generated output. This is a read-only Git query, not a Git mutation.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo 'release requires a clean tracked worktree' >&2
  exit 1
fi
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
  echo 'release requires no untracked files' >&2
  exit 1
fi

version=${VERSION:-$(awk '/^## \[/{gsub(/[^0-9.]/, "", $2); print $2; exit}' CHANGELOG.md)}
[ -n "$version" ] || { echo 'VERSION or CHANGELOG version is required' >&2; exit 1; }
case "$version" in
  *[!0-9.]*|'') echo "invalid version: $version" >&2; exit 1 ;;
esac

./scripts/check-licenses.py --strict
mkdir -p dist
archive="freshmesh-dxos-v${version}-source.tar.gz"
tmp="dist/.${archive}.tmp"
rm -f "$tmp" "dist/$archive" dist/SHA256SUMS dist/sbom.cdx.json

# Archive tracked first-party source only. Runtime volumes, credentials, binaries,
# model weights, and generated dist files are never inputs. Keep a deterministic
# release root independent of the checkout directory name.
git ls-files -z \
  ':!:dist/**' ':!:**/.venv/**' ':!:**/node_modules/**' ':!:**/data/**' \
  ':!:**/secrets/**' ':!:.env' ':!:.env.local' ':!:.env.production' \
  ':!:*.pem' ':!:*.key' ':!:*.crt' ':!:*.p12' ':!:*.jks' \
  | tar --no-recursion --null --transform="s,^,freshmesh-dxos-v${version}/," -czf "$tmp" --files-from=-
mv "$tmp" "dist/$archive"
sha256sum "dist/$archive" > dist/SHA256SUMS

python3 scripts/sbom.py "$version" dist/sbom.cdx.json

printf '%s\n' "wrote dist/$archive, dist/SHA256SUMS, and dist/sbom.cdx.json"
