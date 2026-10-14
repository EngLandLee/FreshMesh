#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
set -eu

repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo"

printf '%s\n' '== backend unit tests =='
if command -v uv >/dev/null 2>&1; then
  uv run --project backend pytest backend/tests
else
  printf '%s\n' 'uv is required for backend tests (install uv or use the CI image)' >&2
  exit 1
fi

printf '%s\n' '== backend lint =='
uv run --project backend ruff check --config backend/pyproject.toml backend

printf '%s\n' '== portal JavaScript syntax =='
node --check portal/app.js

printf '%s\n' '== Compose model =='
docker compose config --quiet

printf '%s\n' '== Apache headers, source boundary, and forbidden artifacts =='
python3 scripts/check-licenses.py --strict

printf '%s\n' 'verification passed'
