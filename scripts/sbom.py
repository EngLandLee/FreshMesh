#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Generate honest CycloneDX metadata from checked-in manifests only.

This is not an image SBOM. The release artifact includes the Python lock set,
workflow POM direct dependencies, and pinned Compose images. CI Syft separately
scans source manifests; neither output claims all compiled image dependencies.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {'m': 'http://maven.apache.org/POM/4.0.0'}


def component(kind: str, name: str, version: str | None, *, purl: str | None = None,
              scope: str | None = None, properties: dict[str, str] | None = None) -> dict:
    item = {'type': kind, 'name': name}
    if version:
        item['version'] = version
    if purl:
        item['purl'] = purl
    if scope:
        item['scope'] = scope
    if properties:
        item['properties'] = [{'name': key, 'value': value} for key, value in properties.items()]
    return item


def python_components() -> list[dict]:
    lock = tomllib.loads((ROOT / 'backend/uv.lock').read_text(encoding='utf-8'))
    result = []
    for package in lock.get('package', []):
        name, version = package.get('name'), package.get('version')
        if name and version:
            result.append(component('library', name, version,
                                    purl=f'pkg:pypi/{name}@{version}', scope='required',
                                    properties={'source': 'backend/uv.lock'}))
    return result

def node_components() -> list[dict]:
    lock = json.loads((ROOT / 'package-lock.json').read_text(encoding='utf-8'))
    result = []
    for path, package in lock.get('packages', {}).items():
        if not path:
            continue
        name = path.split('node_modules/')[-1]
        entry = component('library', name, package.get('version'), scope='optional',
                          properties={'source': 'package-lock.json', 'purpose': 'browser verification only'})
        if package.get('license'):
            entry['licenses'] = [{'expression': package['license']}]
        result.append(entry)
    return result



def maven_components() -> list[dict]:
    root = ET.parse(ROOT / 'workflow/pom.xml').getroot()
    parent_version = root.findtext('m:parent/m:version', namespaces=NS)
    properties = {node.tag.rsplit('}', 1)[-1]: (node.text or '')
                  for node in root.findall('m:properties/*', NS)}
    result = []
    for dep in root.findall('m:dependencies/m:dependency', NS):
        group = dep.findtext('m:groupId', namespaces=NS)
        artifact = dep.findtext('m:artifactId', namespaces=NS)
        version = dep.findtext('m:version', namespaces=NS)
        scope = dep.findtext('m:scope', namespaces=NS) or 'compile'
        if version and version.startswith('${') and version.endswith('}'):
            version = properties.get(version[2:-1], version)
        props = {'source': 'workflow/pom.xml', 'dependencyScope': scope}
        if not version:
            props['versionSource'] = f'managed by Spring Boot parent {parent_version}'
        if group and artifact:
            result.append(component('library', f'{group}:{artifact}', version,
                                    purl=(f'pkg:maven/{group}/{artifact}@{version}' if version else None),
                                    scope='required', properties=props))
    return result


def compose_components() -> list[dict]:
    # Compose is deliberately parsed without PyYAML so release generation has no
    # unlisted dependency. Only pinned image entries are included; build contexts
    # are not mistaken for a published image.
    text = (ROOT / 'compose.yaml').read_text(encoding='utf-8')
    services = re.findall(r'^  ([A-Za-z0-9_-]+):\s*\n((?:    .*\n|\n)*)', text, re.MULTILINE)
    result = []
    for service, body in services:
        match = re.search(r'^    image:\s*([^\s#]+)', body, re.MULTILINE)
        if not match:
            continue
        image = match.group(1)
        name, version = image.rsplit(':', 1) if ':' in image.rsplit('/', 1)[-1] else (image, None)
        result.append(component('container', name, version,
                                purl=f'pkg:docker/{name}@{version}' if version else None,
                                scope='required', properties={'source': 'compose.yaml', 'service': service}))
    return result


def main() -> int:
    if len(sys.argv) != 3:
        print('usage: sbom.py VERSION OUTPUT', file=sys.stderr)
        return 2
    version, output = sys.argv[1:]
    components = python_components() + node_components() + maven_components() + compose_components()
    # Stable ordering makes metadata review and checksums reproducible.
    components.sort(key=lambda item: (item['type'], item['name'], item.get('version', '')))
    doc = {
        'bomFormat': 'CycloneDX', 'specVersion': '1.5', 'version': 1,
        'metadata': {
            'component': {'type': 'application', 'name': 'freshmesh-dxos', 'version': version},
            'properties': [
                {'name': 'scope', 'value': 'Python and browser-tool locks, direct Maven POM dependencies, pinned Compose images'},
                {'name': 'limitation', 'value': 'Direct Maven metadata and container tags; not a complete image or Maven transitive SBOM'},
            ],
        },
        'components': components,
    }
    Path(output).write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {output} with {len(components)} manifest components')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
