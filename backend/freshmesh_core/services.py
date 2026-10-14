# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Identity, workflow and object-storage integration; no service substitutes."""

import os
import uuid
from dataclasses import dataclass
from functools import lru_cache

import boto3
import httpx
import jwt
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import Request


class Fault(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


@dataclass(frozen=True)
class Principal:
    user_id: str
    username: str
    role: str
    chain_id: str
    store_id: str | None = None

    def owner(self):
        if self.role != "owner":
            raise Fault(403, "forbidden_role", "Chỉ chủ chuỗi được thực hiện thao tác này.")


@lru_cache(maxsize=1)
def jwks():
    return jwt.PyJWKClient(os.environ["KEYCLOAK_JWKS_URL"], cache_keys=True, lifespan=300, timeout=5)


def decode_identity(token, client=None):
    try:
        key = (client or jwks()).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience="freshmesh-api",
            issuer=os.environ["KEYCLOAK_ISSUER"],
            options={"require": ["sub", "exp", "iat", "iss", "aud"]},
        )
    except jwt.PyJWKClientConnectionError:
        raise Fault(503, "identity_unavailable", "Dịch vụ định danh chưa sẵn sàng.") from None
    except (jwt.PyJWTError, ValueError, KeyError):
        raise Fault(401, "invalid_token", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.") from None
    roles = set(claims.get("realm_access", {}).get("roles", []))
    allowed = roles & {"owner", "store_manager", "driver"}
    if len(allowed) != 1 or claims.get("chain_id") not in {"CHAIN_A", "CHAIN_B"}:
        raise Fault(403, "identity_scope", "Danh tính thiếu vai trò hoặc phạm vi chuỗi hợp lệ.")
    role = allowed.pop()
    store = claims.get("store_id") or None
    if role == "store_manager" and not store:
        raise Fault(403, "identity_scope", "Quản lý chưa được gán cửa hàng.")
    username = claims.get("preferred_username")
    if not isinstance(username, str) or not username:
        raise Fault(403, "identity_scope", "Danh tính thiếu tên tài khoản.")
    return Principal(claims["sub"], username, role, claims["chain_id"], store)


def identity(request: Request):
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise Fault(401, "unauthorized", "Bạn cần đăng nhập SSO.")
    return decode_identity(token)


@lru_cache(maxsize=1)
def objects():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=3,
            read_timeout=5,
            retries={"max_attempts": 0},
        ),
    )


def bucket():
    return os.environ.get("S3_BUCKET", "freshmesh-documents")


def ensure_bucket():
    try:
        objects().head_bucket(Bucket=bucket())
    except ClientError as exc:
        if exc.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
            raise
        objects().create_bucket(Bucket=bucket())


def workflow_request(path, payload=None):
    try:
        with httpx.Client(base_url=os.environ["WORKFLOW_URL"], timeout=10) as client:
            response = client.get(path) if payload is None else client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError):
        raise Fault(
            503,
            "workflow_unavailable",
            "Workflow không xác nhận thao tác; chưa ghi thay đổi. "
            "Có thể thử lại cùng thao tác sau khi dịch vụ phục hồi.",
        ) from None


def start_workflow(transfer_id):
    return workflow_request("/processes", {"business_key": str(transfer_id)})["process_id"]


def advance_workflow(transfer, task, actor, note="", approved=None):
    # A retry is idempotent only for the same decision, actor and evidence.
    payload = {
        "task": task,
        "actor": actor,
        "note": note,
        "operation_id": str(uuid.uuid5(uuid.NAMESPACE_URL,
            f"{transfer['id']}:{task}:{actor}:{note}:{approved}")),
    }
    if approved is not None:
        payload["approved"] = approved
    result = workflow_request(f"/processes/{transfer['process_id']}/complete", payload)
    expected = {"approval": "dispatch" if approved else None,
                "dispatch": "delivery", "delivery": "receipt", "receipt": None}[task]
    if result.get("task") != expected or bool(result.get("ended")) != (expected is None):
        raise Fault(503, "workflow_conflict", "Workflow và dữ liệu chưa đồng bộ; cần kiểm tra quy trình.")
    return result
