#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Build a static showcase from original source and real browser evidence."""
from pathlib import Path
import argparse
import re
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--screenshots', type=Path, default=ROOT / 'dist/screenshots')
parser.add_argument('--output', type=Path, default=ROOT / 'dist/site')
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
html = (ROOT / 'website/index.html').read_text()
pattern = r'https://github\.com/EngLandLee/FreshMesh-DXOS/releases/download/v[0-9.]+/([a-z0-9-]+\.png)'
images = sorted(set(re.findall(pattern, html)))
shots = args.screenshots.resolve()
shots.mkdir(parents=True, exist_ok=True)
for name in images:
    path = shots / name
    if not path.exists():
        url = next(match.group(0) for match in re.finditer(pattern, html) if match.group(1) == name)
        # Public, versioned project assets only. Failure is not replaced with a mock image.
        urllib.request.urlretrieve(url, path)
    if path.stat().st_size == 0:
        raise SystemExit(f'empty screenshot: {path}')
html = re.sub(pattern, lambda match: f'screenshots/{match.group(1)}', html)
(out / 'index.html').write_text(html)
shutil.copyfile(ROOT / 'website/styles.css', out / 'styles.css')
shutil.copytree(ROOT / 'website/assets', out / 'assets', dirs_exist_ok=True)
shutil.copytree(shots, out / 'screenshots', dirs_exist_ok=True)
shutil.copyfile(ROOT / 'LICENSE', out / 'LICENSE')
print(f'built {out}; {len(images)} referenced real screenshots, original SVG banner and Apache license')
