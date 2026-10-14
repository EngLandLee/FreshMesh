#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Audit source headers and reject release inputs that cannot be distributed."""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {'.py', '.js', '.mjs', '.css', '.html', '.java', '.sh', '.yml', '.yaml', '.toml',
                   '.sql', '.xml', '.properties', '.md', '.json', '.lock'}
SOURCE_NAMES = {'Makefile', 'Dockerfile', 'compose.yaml', 'compose.yml', '.env.example', '.dockerignore'}
SKIP_PARTS = {'.git', 'dist', '__pycache__', 'node_modules', 'target', '.venv', 'data', 'secrets',
              '.ruff_cache', '.pytest_cache'}
FORBIDDEN_SUFFIXES = {'.pem', '.key', '.crt', '.p12', '.jks', '.sqlite3', '.db'}
BINARY_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.zip', '.gz', '.tar', '.woff', '.woff2', '.exe'}


def files() -> list[pathlib.Path]:
    result = []
    for path in ROOT.rglob('*'):
        if not path.is_file() or SKIP_PARTS.intersection(path.parts):
            continue
        if path.suffix.lower() in SOURCE_SUFFIXES or path.name in SOURCE_NAMES:
            result.append(path)
    return sorted(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--strict', action='store_true', help='also reject binary/credential-like files')
    args = parser.parse_args()
    errors: list[str] = []
    for path in files():
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            errors.append(f'{path.relative_to(ROOT)}: not UTF-8 text')
            continue
        if path.suffix == '.json':
            try:
                json.loads(text)
            except json.JSONDecodeError as error:
                errors.append(f'{path.relative_to(ROOT)}: invalid JSON: {error}')
        sidecar = path.with_name(path.name + '.license')
        header = sidecar.read_text(encoding='utf-8') if sidecar.exists() else '\n'.join(text.splitlines()[:30])
        if 'SPDX-License-Identifier: Apache-2.0' not in header:
            errors.append(f'{path.relative_to(ROOT)}: missing SPDX-License-Identifier: Apache-2.0')
        if ('Copyright 2026 FreshMesh-DXOS contributors' not in header
                and 'SPDX-FileCopyrightText: 2026 FreshMesh-DXOS contributors' not in header):
            errors.append(f'{path.relative_to(ROOT)}: missing 2026 FreshMesh-DXOS copyright')
    if args.strict:
        if (ROOT / '.git').exists():
            tracked = subprocess.run(['git', 'ls-files'], cwd=ROOT, check=True,
                                     capture_output=True, text=True).stdout.splitlines()
            for name in tracked:
                path = pathlib.Path(name)
                if ((path.name.startswith('.env') and path.name != '.env.example')
                        or SKIP_PARTS.intersection(path.parts)
                        or path.suffix.lower() in FORBIDDEN_SUFFIXES):
                    errors.append(f'{name}: tracked runtime/secret artifact')
        for path in ROOT.rglob('*'):
            if not path.is_file() or SKIP_PARTS.intersection(path.parts):
                continue
            if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.suffix.lower() in BINARY_SUFFIXES:
                errors.append(f'{path.relative_to(ROOT)}: forbidden credential/binary artifact')
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f'checked {len(files())} source/config files; Apache headers present')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
