#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Exercise the real OLP HTTP stack without fixtures or fabricated responses."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class DemoError(RuntimeError):
    pass


class Demo:
    def __init__(self, base: str, restart: bool) -> None:
        self.base = base.rstrip('/')
        self.restart = restart
        self.tokens: dict[str, str] = {}
        self.users = {
            'manager': os.getenv('DEMO_MANAGER', 'manager_a1'),
            'owner': os.getenv('DEMO_OWNER', 'owner_a'),
            'driver': os.getenv('DEMO_DRIVER', 'driver_a'),
            'other_owner': os.getenv('DEMO_OTHER_OWNER', 'owner_b'),
            'destination_manager': os.getenv('DEMO_DESTINATION_MANAGER', 'manager_a2'),
        }
        self.password = os.getenv('DEMO_PASSWORD', 'demo123')

    def request(self, method: str, path: str, user: str | None = None, body: bytes | None = None,
                content_type: str = 'application/json', expected: set[int] | None = None,
                retry_auth: bool = True, token_override: str | None = None) -> tuple[int, bytes, dict | None]:
        headers = {'Accept': 'application/json'}
        if body is not None:
            headers['Content-Type'] = content_type
        if token_override is not None:
            headers['Authorization'] = f'Bearer {token_override}'
        elif user:
            headers['Authorization'] = f'Bearer {self.token(user)}'
        request = urllib.request.Request(self.base + path, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                status, payload = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, payload = error.code, error.read()
        if status == 401 and user and retry_auth and token_override is None:
            # A signed token can expire while a demo is running. Refresh once; a
            # mutating request is retried only after a pre-handler 401, so the API
            # has not applied a stock effect yet.
            self.tokens.pop(user, None)
            return self.request(method, path, user, body, content_type, expected, False)
        parsed = None
        if payload:
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                pass
        if expected is not None and status not in expected:
            raise DemoError(f'{method} {path}: expected {sorted(expected)}, got {status}: {payload[:500]!r}')
        return status, payload, parsed

    def token(self, username: str) -> str:
        if username in self.tokens:
            return self.tokens[username]
        realm = os.getenv('KEYCLOAK_TOKEN_URL', self.base + '/auth/realms/freshmesh/protocol/openid-connect/token')
        values = urllib.parse.urlencode({
            'grant_type': 'password', 'client_id': os.getenv('DEMO_CLIENT_ID', 'freshmesh-portal'),
            'username': username, 'password': self.password,
        }).encode()
        request = urllib.request.Request(realm, data=values, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read())
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as error:
            raise DemoError(f'cannot obtain demo token for {username}: {error}') from error
        token = payload.get('access_token')
        if not token:
            raise DemoError(f'token response for {username} had no access_token')
        self.tokens[username] = token
        return token

    @staticmethod
    def json_bytes(value: object) -> bytes:
        return json.dumps(value, separators=(',', ':')).encode()

    def overview(self, user: str) -> dict:
        _, _, payload = self.request('GET', '/api/overview', user, expected={200})
        if not isinstance(payload, dict) or not isinstance(payload.get('stock'), list):
            raise DemoError('overview response has no stock list')
        return payload

    def workflow(self, transfer_id: str, user: str, task: str | None) -> None:
        _, _, state = self.request('GET', f'/api/core/workflows/{transfer_id}', user, expected={200})
        if state.get('task') != task or bool(state.get('ended')) != (task is None):
            raise DemoError(f'Flowable task mismatch: wanted {task}, received {state}')

    def run(self) -> None:
        self.request('GET', '/api/config', expected={200})
        _, _, health = self.request('GET', '/api/health', expected={200})
        if health.get('status') != 'ok' or not all(health.get('services', {}).get(key)
                for key in ('database', 'identity', 'storage', 'workflow', 'gateway')):
            raise DemoError(f'Not all mandatory services are ready: {health}')
        self.request('GET', '/api/me', expected={401, 403})
        self.request('GET', '/api/me', token_override='not-a-signed-token', expected={401, 403})
        manager = self.users['manager']
        owner = self.users['owner']
        other = self.users['other_owner']
        _, _, manager_identity = self.request('GET', '/api/me', user=manager, expected={200})
        source_id = manager_identity.get('store_id') if isinstance(manager_identity, dict) else None
        if not source_id:
            raise DemoError('demo manager has no store scope')
        before = self.overview(owner)
        self.request('GET', '/api/transfers', user=other, expected={200})
        stock = [row for row in before['stock']
                 if row.get('store_id') == source_id and float(row.get('available', 0)) >= 2]
        if not stock:
            raise DemoError(f'no source lot with two available units for manager store {source_id}')
        source = stock[0]
        chain_stores = [row for row in before.get('stores', []) if row.get('id') != source_id]
        target = next((row for row in chain_stores if str(row.get('id', '')).startswith('A-')), None)
        if target is None:
            raise DemoError(f'no same-chain destination store for source {source_id}')
        target_id = target['id']
        if 'DEMO_DESTINATION_MANAGER' not in os.environ:
            self.users['destination_manager'] = {'A-01': 'manager_a1', 'A-02': 'manager_a2'}.get(target_id, manager)
        quantity = 2
        rejection_probe = self.json_bytes({
            'source_store_id': source_id, 'target_store_id': target_id,
            'lot_id': source['lot_id'], 'quantity': 1, 'note': 'PoF reservation release probe',
        })
        _, _, rejected = self.request('POST', '/api/transfers', manager, rejection_probe, expected={200, 201})
        if not isinstance(rejected, dict) or not rejected.get('id'):
            raise DemoError('reservation probe returned no transfer ID')
        self.request('POST', f'/api/transfers/{rejected["id"]}/approve', owner,
                     self.json_bytes({'decision': 'rejected', 'note': 'PoF reservation release'}), expected={200, 201})
        after_rejection = self.overview(owner)
        source_rejection = next((r for r in after_rejection['stock']
                                 if r.get('lot_id') == source['lot_id'] and r.get('store_id') == source_id), None)
        if source_rejection is None or source_rejection.get('quantity') != source.get('quantity') \
                or source_rejection.get('reserved') != source.get('reserved'):
            raise DemoError('rejected transfer did not release its reservation')
        transfer_body = self.json_bytes({
            'source_store_id': source_id, 'target_store_id': target_id,
            'lot_id': source['lot_id'], 'quantity': quantity,
            'note': 'PoF real-stack demo',
        })
        _, _, transfer = self.request('POST', '/api/transfers', manager, transfer_body, expected={200, 201})
        if not isinstance(transfer, dict) or not transfer.get('id'):
            raise DemoError('create transfer returned no ID')
        transfer_id = transfer['id']
        self.workflow(transfer_id, owner, 'approval')
        excessive = self.json_bytes({'source_store_id': source_id, 'target_store_id': target_id,
                                     'lot_id': source['lot_id'], 'quantity': int(source['quantity']) + 1})
        self.request('POST', '/api/transfers', manager, excessive, expected={409})

        # Cross-chain command must be denied, not silently accepted.
        cross = self.json_bytes({'source_store_id': source_id, 'target_store_id': 'B-01',
                                 'lot_id': source['lot_id'], 'quantity': 1})
        self.request('POST', '/api/transfers', other, cross, expected={401, 403})
        self.request('POST', f'/api/transfers/{transfer_id}/approve', manager,
                     self.json_bytes({'decision': 'approved', 'note': 'self-approval must fail'}), expected={401, 403, 409})

        content = f'FreshMesh demo receipt {uuid.uuid4()}\n'.encode()
        boundary = '----freshmesh-' + uuid.uuid4().hex
        multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="receipt.txt"\r\n'
                     'Content-Type: text/plain\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
        self.request('POST', f'/api/transfers/{transfer_id}/documents', manager, multipart,
                     f'multipart/form-data; boundary={boundary}', expected={200, 201})
        _, _, listed = self.request('GET', '/api/transfers', manager, expected={200})
        current = next((item for item in listed or [] if str(item.get('id')) == str(transfer_id)), None)
        docs = current.get('documents', []) if isinstance(current, dict) else []
        if not docs:
            raise DemoError('uploaded document cannot be found for checksum verification')
        reported_sha = docs[-1].get('sha256')
        content_sha = hashlib.sha256(content).hexdigest()
        if reported_sha and reported_sha != content_sha:
            raise DemoError(f'API document checksum {reported_sha} differs from upload {content_sha}')
        self.request('GET', f'/api/transfers/{transfer_id}/documents/{docs[-1]["id"]}', other, expected={401, 403})
        _, downloaded, _ = self.request('GET', f'/api/transfers/{transfer_id}/documents/{docs[-1]["id"]}', manager, expected={200})
        if hashlib.sha256(downloaded).hexdigest() != content_sha:
            raise DemoError('document checksum changed during download')

        self.request('POST', f'/api/transfers/{transfer_id}/approve', owner,
                     self.json_bytes({'decision': 'approved', 'note': 'PoF owner approval'}), expected={200, 201})
        self.workflow(transfer_id, owner, 'dispatch')
        _, _, route = self.request('POST', '/api/routes', owner,
                                   self.json_bytes({'transfer_ids': [transfer_id], 'driver_username': self.users['driver']}), expected={200, 201})
        if not isinstance(route, dict) or not route.get('id'):
            raise DemoError('route creation returned no ID')
        self.request('POST', f'/api/routes/{route["id"]}/dispatch', owner, self.json_bytes({}), expected={200, 201})
        self.workflow(transfer_id, owner, 'delivery')
        actual = max(1, quantity - 1)
        self.request('POST', f'/api/transfers/{transfer_id}/deliver', self.users['driver'],
                     self.json_bytes({'actual_quantity': actual, 'note': 'short delivery' if actual < quantity else 'delivery'}), expected={200, 201})
        self.workflow(transfer_id, owner, 'receipt')
        self.request('POST', f'/api/transfers/{transfer_id}/receive', self.users['destination_manager'],
                     self.json_bytes({'actual_quantity': actual, 'note': 'receipt'}), expected={200, 201})
        self.workflow(transfer_id, owner, None)
        self.request('POST', f'/api/transfers/{transfer_id}/receive', self.users['destination_manager'],
                     self.json_bytes({'actual_quantity': actual, 'note': 'duplicate must conflict'}), expected={409})

        after = self.overview(owner)
        source_before = next((r for r in before['stock'] if r.get('lot_id') == source['lot_id'] and r.get('store_id') == source_id), None)
        source_after = next((r for r in after['stock'] if r.get('lot_id') == source['lot_id'] and r.get('store_id') == source_id), None)
        if source_before is None or source_after is None:
            raise DemoError('source lot disappeared after dispatch')
        source_qty_delta = float(source_before.get('quantity', 0)) - float(source_after.get('quantity', 0))
        source_reserved_delta = float(source_before.get('reserved', 0)) - float(source_after.get('reserved', 0))
        if source_qty_delta != quantity:
            raise DemoError(f'source quantity changed by {source_qty_delta}, expected {quantity}')
        if source_reserved_delta != 0:
            raise DemoError('source reservation was not released after dispatch')
        destination_before = sum(float(r.get('quantity', 0)) for r in before['stock'] if r.get('store_id') == target_id)
        destination_after = sum(float(r.get('quantity', 0)) for r in after['stock'] if r.get('store_id') == target_id)
        if destination_after - destination_before != actual:
            raise DemoError(f'destination quantity changed by {destination_after - destination_before}, expected {actual}')

        if self.restart:
            subprocess.run(['docker', 'compose', 'restart', 'api'], check=True)
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                status, _, ready = self.request('GET', '/api/health')
                if status == 200 and isinstance(ready, dict) and ready.get('status') == 'ok':
                    break
                time.sleep(1)
            else:
                raise DemoError('API did not become ready within 60s after restart')
            _, _, transfers = self.request('GET', '/api/transfers', manager, expected={200})
            if not any(str(item.get('id')) == str(transfer_id) for item in (transfers or [])):
                raise DemoError('transfer disappeared after API restart')
            self.workflow(transfer_id, owner, None)
            _, persisted_bytes, _ = self.request('GET',
                f'/api/transfers/{transfer_id}/documents/{docs[-1]["id"]}', manager, expected={200})
            if hashlib.sha256(persisted_bytes).hexdigest() != content_sha:
                raise DemoError('document changed after restart')
        print(f'demo passed: transfer={transfer_id} source={source_id} target={target_id} actual={actual}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default=os.getenv('PORTAL_URL', 'http://localhost:3180'))
    parser.add_argument('--skip-restart', action='store_true')
    args = parser.parse_args()
    try:
        Demo(args.base_url, restart=not args.skip_restart).run()
    except (DemoError, OSError, subprocess.CalledProcessError) as error:
        print(f'demo failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
