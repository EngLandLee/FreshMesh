#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Audit every distributable first-party file and reject unsafe release inputs.

The normal audit follows tracked files in a checkout.  In a source archive (where
``.git`` is absent), it follows every file in the tree except explicitly generated
or runtime directories. JSON and TOML lock files are parsed, while
format-constrained and standard legal text may carry a ``.license`` sidecar
instead of inline comments.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEADER_LINES = 30
SIDECAR_SUFFIX = '.license'
SIDECAR_FORMATS = {'.json', '.lock'}
COPYRIGHT = '2026 FreshMesh-DXOS contributors'
SPDX = 'SPDX-License-Identifier: Apache-2.0'

# These directories are generated, cached, or runtime state rather than source
# distribution inputs.  Keep names component-based so the same policy works in
# a checkout and in a downloaded source archive without .git.
SKIP_PARTS = {
    '.git', 'dist', 'node_modules', 'target', '.venv', '.venvs', 'venv', 'venvs',
    '.virtualenv', 'virtualenv', 'env', '__pycache__', '.pytest_cache',
    '.ruff_cache', '.mypy_cache', '.cache', 'cache', 'caches', 'coverage',
    'htmlcov', '.volumes', '.ollama', 'models', 'data', 'secrets',
}
LEGAL_TEXT_NAMES = {'LICENSE', 'NOTICE', 'COPYING'}
FORBIDDEN_SUFFIXES = {
    '.pem', '.key', '.crt', '.p12', '.jks', '.sqlite', '.sqlite3', '.db', '.log',
}
BINARY_SUFFIXES = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.zip', '.gz', '.tar',
    '.7z', '.rar', '.iso', '.bin', '.mp3', '.mp4', '.mov', '.avi', '.wasm',
    '.woff', '.woff2', '.exe', '.dll', '.so', '.dylib', '.class', '.pyc',
}


def skipped(path: pathlib.Path) -> bool:
    return bool(SKIP_PARTS.intersection(path.parts))


def tracked_paths() -> list[pathlib.Path]:
    """Return tracked paths, preserving arbitrary names and extensionless files."""
    output = subprocess.run(
        ['git', 'ls-files', '-z'],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    names = output.decode(errors='surrogateescape').split('\0')
    return [ROOT / pathlib.Path(name) for name in names if name]


def files() -> list[pathlib.Path]:
    """Return distributable files, using the archive-safe fallback without .git."""
    if (ROOT / '.git').exists():
        paths = tracked_paths()
    else:
        paths = [path for path in ROOT.rglob('*') if path.is_file()]
    return sorted(path for path in paths if not skipped(path.relative_to(ROOT)))


def read_text(path: pathlib.Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f'{path.relative_to(ROOT)}: not UTF-8 text ({error})')
        return None


def valid_metadata(text: str) -> bool:
    header = '\n'.join(text.splitlines()[:HEADER_LINES])
    return SPDX in header and (
        f'Copyright {COPYRIGHT}' in header
        or f'SPDX-FileCopyrightText: {COPYRIGHT}' in header
    )


def sidecar_for(path: pathlib.Path) -> pathlib.Path:
    return path.with_name(path.name + SIDECAR_SUFFIX)


def is_legal_text(path: pathlib.Path) -> bool:
    return path.name.upper() in LEGAL_TEXT_NAMES


def audit_sidecar(
    path: pathlib.Path,
    errors: list[str],
    available: set[pathlib.Path],
) -> None:
    text = read_text(path, errors)
    if text is None:
        return
    target = path.with_name(path.name[:-len(SIDECAR_SUFFIX)])
    if target not in available:
        errors.append(f'{path.relative_to(ROOT)}: sidecar target is not distributable/tracked')
    if not valid_metadata(text):
        errors.append(
            f'{path.relative_to(ROOT)}: invalid license sidecar '
            f'(requires {SPDX} and copyright)'
        )


def audit_file(
    path: pathlib.Path,
    errors: list[str],
    available: set[pathlib.Path],
) -> None:
    relative = path.relative_to(ROOT)
    if path.name.endswith(SIDECAR_SUFFIX):
        audit_sidecar(path, errors, available)
        return
    text = read_text(path, errors)
    if text is None:
        return
    if path.suffix.lower() == '.json':
        try:
            json.loads(text)
        except json.JSONDecodeError as error:
            errors.append(f'{relative}: invalid JSON: {error}')
    elif path.suffix.lower() == '.lock':
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            errors.append(f'{relative}: invalid TOML lock file: {error}')

    sidecar = sidecar_for(path)
    if sidecar in available:
        if path.suffix.lower() not in SIDECAR_FORMATS and not is_legal_text(path):
            errors.append(
                f'{sidecar.relative_to(ROOT)}: sidecars are only allowed for '
                'JSON/lock files and standardized legal text'
            )
        return
    if sidecar.exists():
        errors.append(f'{sidecar.relative_to(ROOT)}: sidecar is not distributable/tracked')
    elif is_legal_text(path):
        errors.append(f'{relative}: missing {SIDECAR_SUFFIX} sidecar for legal text')
    elif not valid_metadata(text):
        errors.append(
            f'{relative}: missing {SPDX} and copyright in first '
            f'{HEADER_LINES} lines (or a valid {SIDECAR_SUFFIX} sidecar)'
        )


def binary(path: pathlib.Path) -> bool:
    try:
        data = path.read_bytes()
        data.decode('utf-8')
    except (OSError, UnicodeDecodeError):
        return True
    return b'\0' in data


def strict_boundary(errors: list[str]) -> None:
    """Reject credentials and binary artifacts in tracked or archive inputs."""
    checkout = (ROOT / '.git').exists()
    tracked = set(tracked_paths()) if checkout else set()
    if (ROOT / '.git').exists():
        for path in tracked_paths():
            relative = path.relative_to(ROOT)
            if skipped(relative):
                errors.append(f'{relative}: tracked runtime/generated artifact')
    candidates = [path for path in ROOT.rglob('*') if path.is_file()]

    for path in candidates:
        relative = path.relative_to(ROOT)
        if skipped(relative):
            continue
        lower = path.name.lower()
        suffix = path.suffix.lower()
        private_env = lower.startswith('.env') and lower != '.env.example'
        if (private_env and (not checkout or path in tracked)) or suffix in FORBIDDEN_SUFFIXES:
            errors.append(f'{relative}: forbidden credential/runtime artifact')
        if suffix in BINARY_SUFFIXES or binary(path):
            errors.append(f'{relative}: forbidden binary artifact')


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Audit all distributed first-party source/config/docs files. '
            'Generated/runtime directories are excluded; --strict also rejects '
            'credential-like and binary artifacts.'
        )
    )
    parser.add_argument('--strict', action='store_true',
                        help='also reject binary/credential-like files')
    args = parser.parse_args()
    errors: list[str] = []
    distribution = files()
    available = set(distribution)
    for path in distribution:
        audit_file(path, errors, available)
    if args.strict:
        strict_boundary(errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f'checked {len(distribution)} distributable first-party files; metadata present')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
