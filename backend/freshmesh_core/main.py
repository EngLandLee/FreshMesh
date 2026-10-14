# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Original DX-OS API. Public surface goes through APISIX; no end-user UI here."""

import hashlib
import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Annotated, Literal
from urllib.parse import quote

import httpx
import psycopg
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field

from freshmesh_core import __version__, decisions, transfers
from freshmesh_core.db import connect, initialize
from freshmesh_core.services import (
    Fault,
    Principal,
    bucket,
    ensure_bucket,
    identity,
    objects,
    start_workflow,
    workflow_request,
)

log = logging.getLogger("freshmesh")
Actor = Annotated[Principal, Depends(identity)]
Document = Annotated[UploadFile, File()]


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TransferBody(Body):
    source_store_id: str = Field(min_length=1, max_length=64)
    target_store_id: str = Field(min_length=1, max_length=64)
    lot_id: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=10000, strict=True)
    note: str = Field(default="", max_length=1000)


class ApprovalBody(Body):
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=1000)


class DispatchBody(Body):
    driver_username: str = Field(min_length=1, max_length=64)


class ReceiptBody(Body):
    actual_quantity: int = Field(ge=0, le=10000, strict=True)
    note: str = Field(default="", max_length=1000)


class RouteBody(DispatchBody):
    transfer_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


class ChatBody(Body):
    message: str = Field(min_length=1, max_length=2000)


@asynccontextmanager
async def lifespan(app):
    initialize()
    ensure_bucket()
    yield


app = FastAPI(
    title="FreshMesh-DXOS Headless API", version=__version__, lifespan=lifespan,
    docs_url=None, redoc_url=None, openapi_url=None
)


@app.exception_handler(Fault)
async def fault_handler(request, exc):
    return JSONResponse(
        status_code=exc.status, content={"error": {"code": exc.code, "message_vi": exc.message}}
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "invalid_input",
                "message_vi": "Dữ liệu không hợp lệ; kiểm tra số lượng và các trường bắt buộc.",
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_handler(request, exc):
    log.exception("Request failed: %s", request.url.path, exc_info=exc)
    status = 503 if isinstance(exc, (psycopg.OperationalError, BotoCoreError, ClientError)) else 500
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": "service_error",
                "message_vi": "Dịch vụ chưa hoàn thành thao tác. Kiểm tra trạng thái trước khi thử lại.",
            }
        },
    )


@app.get("/api/config")
def config():
    return {
        "issuer": os.environ["KEYCLOAK_ISSUER"],
        "client_id": "freshmesh-portal",
        "name": "FreshMesh-DXOS",
        "version": __version__,
        "hpdi": "P",
    }


@app.get("/api/health")
def health():
    services = {}
    try:
        with connect() as con:
            con.execute("SELECT 1")
        services["database"] = True
    except psycopg.Error:
        services["database"] = False
    for name, url in [
        ("identity", os.environ["KEYCLOAK_JWKS_URL"]),
        ("workflow", os.environ["WORKFLOW_URL"] + "/health"),
        ("gateway", os.environ.get("GATEWAY_URL", "http://gateway:9080") + "/api/config"),
    ]:
        try:
            services[name] = httpx.get(url, timeout=3).status_code == 200
        except httpx.HTTPError:
            services[name] = False
    try:
        objects().head_bucket(Bucket=bucket())
        services["storage"] = True
    except (BotoCoreError, ClientError):
        services["storage"] = False
    return {"status": "ok" if all(services.values()) else "degraded", "services": services}


@app.get("/api/me")
def me(user: Actor):
    return asdict(user)


def lot_rows(con, user, all_chain=False):
    sql = "SELECT *,id AS lot_id,quantity-reserved AS available FROM lots WHERE chain_id=%s"
    args = [user.chain_id]
    if not all_chain and user.role == "store_manager":
        sql += " AND store_id=%s"
        args.append(user.store_id)
    if not all_chain and user.role == "driver":
        return []
    return con.execute(sql + " ORDER BY store_id,expires_on,id", args).fetchall()


def visible_rows(con, user):
    sql = transfers.BASE + "WHERE t.chain_id=%s"
    args = [user.chain_id]
    if user.role == "store_manager":
        sql += " AND (t.source_store_id=%s OR t.target_store_id=%s)"
        args += [user.store_id, user.store_id]
    elif user.role == "driver":
        sql += " AND t.driver_username=%s"
        args.append(user.username)
    return con.execute(sql + " ORDER BY t.created_at DESC", args).fetchall()


@app.get("/api/overview")
def overview(user: Actor):
    with connect() as con:
        counts = {
            key: 0 for key in ["submitted", "approved", "rejected", "dispatched", "delivered", "received"]
        }
        for row in visible_rows(con, user):
            counts[row["status"]] += 1
        return {
            "stores": con.execute(
                "SELECT * FROM stores WHERE chain_id=%s ORDER BY id", (user.chain_id,)
            ).fetchall(),
            "stock": lot_rows(con, user),
            "counts": counts,
            "provenance": decisions.PROVENANCE,
        }


@app.get("/api/recommendations")
def recommendations(user: Actor):
    if user.role == "driver":
        return {"items": [], "method": "Không cấp dữ liệu quyết định cho tài xế", "assumptions": []}
    with connect() as con:
        lots = lot_rows(con, user, all_chain=True)
        sales = con.execute(
            "SELECT store_id,sku,avg(quantity) AS forecast FROM sales WHERE chain_id=%s "
            "AND day>=current_date-7 AND day<current_date GROUP BY store_id,sku",
            (user.chain_id,),
        ).fetchall()
        result = decisions.recommend(lots, sales)
        if user.role == "store_manager":
            result["items"] = [item for item in result["items"] if item["source_store_id"] == user.store_id]
        return result


@app.get("/api/transfers")
def list_transfers(user: Actor):
    with connect() as con:
        return [transfers.detailed(con, row) for row in visible_rows(con, user)]


@app.get("/api/transfers/{transfer_id}")
def transfer_detail(transfer_id: uuid.UUID, user: Actor):
    with connect() as con:
        return transfers.detailed(con, transfers.get_transfer(con, user, transfer_id))


@app.post("/api/transfers", status_code=201)
def create_transfer(body: TransferBody, user: Actor):
    if user.role not in {"owner", "store_manager"}:
        raise Fault(403, "forbidden_role", "Tài xế không được tạo phiếu.")
    if user.role == "store_manager" and body.source_store_id != user.store_id:
        raise Fault(403, "forbidden_store", "Chỉ được xuất từ cửa hàng được gán.")
    if body.source_store_id == body.target_store_id:
        raise Fault(422, "same_store", "Cửa hàng gửi và nhận phải khác nhau.")
    with connect() as con:
        for store in [body.source_store_id, body.target_store_id]:
            if not con.execute(
                "SELECT id FROM stores WHERE id=%s AND chain_id=%s", (store, user.chain_id)
            ).fetchone():
                raise Fault(403, "forbidden_chain", "Cửa hàng không thuộc chuỗi của bạn.")
        lot = con.execute(
            "SELECT * FROM lots WHERE id=%s AND chain_id=%s AND store_id=%s FOR UPDATE",
            (body.lot_id, user.chain_id, body.source_store_id),
        ).fetchone()
        if not lot:
            raise Fault(403, "forbidden_lot", "Lô hàng không thuộc cửa hàng gửi.")
        from datetime import date

        if lot["expires_on"] < date.today():
            raise Fault(409, "expired_lot", "Không được điều chuyển lô đã hết hạn.")
        if lot["quantity"] - lot["reserved"] < body.quantity:
            raise Fault(
                409, "insufficient_stock", "Không đủ hàng khả dụng; có thể đã được giữ cho phiếu khác."
            )
        transfer_id = uuid.uuid4()
        process_id = start_workflow(transfer_id)
        con.execute(
            "INSERT INTO transfers(id,chain_id,source_store_id,target_store_id,lot_id,quantity,"
            "status,created_by,note,process_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                transfer_id,
                user.chain_id,
                body.source_store_id,
                body.target_store_id,
                body.lot_id,
                body.quantity,
                "submitted",
                user.username,
                body.note,
                process_id,
            ),
        )
        con.execute("UPDATE lots SET reserved=reserved+%s WHERE id=%s", (body.quantity, body.lot_id))
        row = transfers.get_transfer(con, user, transfer_id)
        transfers.event(con, row, "submitted", user.username, body.note)
        return transfers.detailed(con, row)


@app.post("/api/transfers/{transfer_id}/approve")
def approve(transfer_id: uuid.UUID, body: ApprovalBody, user: Actor):
    with connect() as con:
        row = transfers.get_transfer(con, user, transfer_id, lock=True)
        transfers.approve(con, user, row, body.decision, body.note)
        return transfers.detailed(con, transfers.get_transfer(con, user, transfer_id))


@app.post("/api/transfers/{transfer_id}/dispatch")
def dispatch(transfer_id: uuid.UUID, body: DispatchBody, user: Actor):
    with connect() as con:
        row = transfers.get_transfer(con, user, transfer_id, lock=True)
        transfers.dispatch(con, user, row, body.driver_username)
        return transfers.detailed(con, transfers.get_transfer(con, user, transfer_id))


@app.post("/api/transfers/{transfer_id}/deliver")
def deliver(transfer_id: uuid.UUID, body: ReceiptBody, user: Actor):
    with connect() as con:
        row = transfers.get_transfer(con, user, transfer_id, lock=True)
        transfers.deliver(con, user, row, body.actual_quantity, body.note)
        return transfers.detailed(con, transfers.get_transfer(con, user, transfer_id))


@app.post("/api/transfers/{transfer_id}/receive")
def receive(transfer_id: uuid.UUID, body: ReceiptBody, user: Actor):
    with connect() as con:
        row = transfers.get_transfer(con, user, transfer_id, lock=True)
        transfers.receive(con, user, row, body.actual_quantity, body.note)
        return transfers.detailed(con, transfers.get_transfer(con, user, transfer_id))


@app.post("/api/transfers/{transfer_id}/documents", status_code=201)
def upload(transfer_id: uuid.UUID, file: Document, user: Actor):
    content = file.file.read(5 * 1024 * 1024 + 1)
    if not content or len(content) > 5 * 1024 * 1024:
        raise Fault(422, "invalid_file", "Tệp phải từ 1 byte đến 5 MiB.")
    filename = (file.filename or "document").replace("\\", "/").split("/")[-1][:200]
    if not filename or any(ord(char) < 32 for char in filename):
        raise Fault(422, "invalid_filename", "Tên tệp không hợp lệ.")
    # Every download is forced to attachment, never rendered as active browser content.
    doc_id = uuid.uuid4()
    key = f"{user.chain_id}/{transfer_id}/{doc_id}"
    checksum = hashlib.sha256(content).hexdigest()
    with connect() as con:
        row = transfers.get_transfer(con, user, transfer_id, lock=True)
        if user.role == "driver" and row["status"] not in {"dispatched", "delivered"}:
            raise Fault(403, "forbidden_document", "Tài xế chỉ bổ sung chứng từ khi giao hàng.")
        objects().put_object(Bucket=bucket(), Key=key, Body=content, ContentType="application/octet-stream")
        con.execute(
            "INSERT INTO documents(id,chain_id,transfer_id,filename,object_key,size,sha256,created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (doc_id, user.chain_id, transfer_id, filename, key, len(content), checksum, user.username),
        )
    return {"id": doc_id, "filename": filename, "size": len(content), "sha256": checksum}


@app.get("/api/transfers/{transfer_id}/documents/{document_id}")
def download(transfer_id: uuid.UUID, document_id: uuid.UUID, user: Actor):
    with connect() as con:
        transfers.get_transfer(con, user, transfer_id)
        doc = con.execute(
            "SELECT * FROM documents WHERE id=%s AND transfer_id=%s AND chain_id=%s",
            (document_id, transfer_id, user.chain_id),
        ).fetchone()
    if not doc:
        raise Fault(404, "not_found", "Không tìm thấy chứng từ.")
    obj = objects().get_object(Bucket=bucket(), Key=doc["object_key"])
    with obj["Body"] as stream:
        content = stream.read()
    if hashlib.sha256(content).hexdigest() != doc["sha256"]:
        raise Fault(503, "document_integrity", "Chứng từ không khớp checksum đã lưu.")
    return Response(
        content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(doc['filename'], safe='')}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@app.get("/api/drivers")
def drivers(user: Actor):
    with connect() as con:
        rows = con.execute(
            "SELECT username,name FROM drivers WHERE chain_id=%s ORDER BY username", (user.chain_id,)
        ).fetchall()
        return [row for row in rows if user.role != "driver" or row["username"] == user.username]


def format_route(row):
    return {
        **row,
        "method": "OR-Tools",
        "assumptions": "Khoảng cách đường chim bay, có quay về điểm gửi; không phải đường bộ/ETA. "
        "Một xe tối đa 40 gói, các phiếu cùng cửa hàng gửi.",
    }


@app.get("/api/routes")
def routes(user: Actor):
    with connect() as con:
        sql = "SELECT * FROM routes WHERE chain_id=%s"
        args = [user.chain_id]
        if user.role == "driver":
            sql += " AND driver_username=%s"
            args.append(user.username)
        elif user.role == "store_manager":
            sql += " AND EXISTS(SELECT 1 FROM transfers t WHERE t.id=ANY(routes.transfer_ids) "
            sql += "AND (source_store_id=%s OR target_store_id=%s))"
            args += [user.store_id, user.store_id]
        return [format_route(row) for row in con.execute(sql + " ORDER BY created_at DESC", args).fetchall()]


@app.post("/api/routes", status_code=201)
def create_route(body: RouteBody, user: Actor):
    user.owner()
    if len(set(body.transfer_ids)) != len(body.transfer_ids):
        raise Fault(422, "duplicate_transfer", "Một phiếu không được xuất hiện hai lần trong tuyến.")
    with connect() as con:
        transfers.driver_valid(con, user, body.driver_username)
        rows = [transfers.get_transfer(con, user, item, lock=True) for item in sorted(body.transfer_ids)]
        for row in rows:
            transfers.require_state(row, "approved")
        if len({row["source_store_id"] for row in rows}) != 1:
            raise Fault(422, "different_sources", "Một tuyến phải bắt đầu từ cùng cửa hàng gửi.")
        if sum(row["quantity"] for row in rows) > 40:
            raise Fault(422, "over_capacity", "Tuyến vượt sức chứa 40 gói; chia thành các chuyến.")
        source = con.execute("SELECT * FROM stores WHERE id=%s", (rows[0]["source_store_id"],)).fetchone()
        grouped = {}
        for row in rows:
            target = row["target_store_id"]
            if target not in grouped:
                store = con.execute("SELECT * FROM stores WHERE id=%s", (target,)).fetchone()
                grouped[target] = {
                    "store_id": target,
                    "name": store["name"],
                    "lat": store["lat"],
                    "lng": store["lng"],
                    "transfer_ids": [],
                }
            grouped[target]["transfer_ids"].append(str(row["id"]))
        stops, distance = decisions.plan_route(source, list(grouped.values()))
        route_id = uuid.uuid4()
        con.execute(
            "INSERT INTO routes(id,chain_id,driver_username,transfer_ids,stops,distance_km) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (route_id, user.chain_id, body.driver_username, body.transfer_ids, Jsonb(stops), distance),
        )
        return format_route(con.execute("SELECT * FROM routes WHERE id=%s", (route_id,)).fetchone())


@app.post("/api/routes/{route_id}/dispatch")
def dispatch_route(route_id: uuid.UUID, user: Actor):
    user.owner()
    with connect() as con:
        row = con.execute("SELECT * FROM routes WHERE id=%s FOR UPDATE", (route_id,)).fetchone()
        if not row:
            raise Fault(404, "not_found", "Không tìm thấy tuyến.")
        if row["chain_id"] != user.chain_id:
            raise Fault(403, "forbidden_chain", "Tuyến không thuộc chuỗi.")
        if row["status"] != "planned":
            raise Fault(409, "invalid_state", "Tuyến đã được điều phối.")
        for transfer_id in sorted(row["transfer_ids"]):
            transfer = transfers.get_transfer(con, user, transfer_id, lock=True)
            transfers.dispatch(con, user, transfer, row["driver_username"])
        con.execute("UPDATE routes SET status='dispatched' WHERE id=%s", (route_id,))
        return format_route({**row, "status": "dispatched"})


@app.get("/api/core/workflows/{transfer_id}")
def workflow_status(transfer_id: uuid.UUID, user: Actor):
    with connect() as con:
        row = transfers.get_transfer(con, user, transfer_id)
    return workflow_request(f"/processes/{row['process_id']}")


@app.post("/api/agent/chat")
def chat(body: ChatBody, user: Actor):
    if user.role == "driver":
        raise Fault(403, "forbidden_role", "Tài xế không được truy vấn tri thức kinh doanh.")
    url = os.environ.get("OLLAMA_URL", "").strip()
    model = os.environ.get("OLLAMA_MODEL", "").strip()
    if not url or not model:
        raise Fault(
            503, "ai_unavailable", "AI tùy chọn chưa được cấu hình. Các quy trình chính vẫn hoạt động."
        )
    context = recommendations(user)
    try:
        result = httpx.post(
            url + "/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": "Bạn hỗ trợ quyết định FreshMesh bằng tiếng Việt. Không thực thi "
                        "hành động, không tự duyệt. Chỉ dùng số liệu trong context; thiếu bằng chứng thì nói không biết. "
                        "Trả lời theo Đề xuất / Vì sao / Độ tin cậy / Giả định / Việc cần duyệt. Context: "
                        + str(context),
                    },
                    {"role": "user", "content": body.message},
                ],
            },
            timeout=120,
        )
        result.raise_for_status()
        answer = result.json()["message"]["content"]
    except (httpx.HTTPError, KeyError, ValueError):
        raise Fault(
            503, "ai_unavailable", "Không nhận được câu trả lời từ mô hình; không tạo câu trả lời giả."
        ) from None
    return {
        "answer": answer,
        "sources": [decisions.PROVENANCE],
        "model": model,
        "warning": "Văn bản AI có thể sai; số liệu và hành động phải đối chiếu, người có quyền duyệt.",
    }
