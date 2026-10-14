# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Human approvals, accountable delivery and real stock effects."""

from datetime import date

from freshmesh_core.services import Fault, advance_workflow

BASE = "SELECT t.*,l.sku,l.name FROM transfers t JOIN lots l ON l.id=t.lot_id "


def scope(principal, row):
    if row["chain_id"] != principal.chain_id:
        raise Fault(403, "forbidden_chain", "Không được truy cập dữ liệu của chuỗi khác.")
    if principal.role == "store_manager" and principal.store_id not in (
        row["source_store_id"],
        row["target_store_id"],
    ):
        raise Fault(403, "forbidden_store", "Phiếu không thuộc cửa hàng của bạn.")
    if principal.role == "driver" and row["driver_username"] != principal.username:
        raise Fault(403, "forbidden_driver", "Phiếu chưa được phân công cho bạn.")


def get_transfer(con, principal, transfer_id, lock=False):
    row = con.execute(
        BASE + "WHERE t.id=%s" + (" FOR UPDATE OF t" if lock else ""), (transfer_id,)
    ).fetchone()
    if not row:
        raise Fault(404, "not_found", "Không tìm thấy phiếu.")
    scope(principal, row)
    return row


def detailed(con, row):
    return {
        **row,
        "events": con.execute(
            "SELECT action,actor,note,at FROM events WHERE transfer_id=%s ORDER BY id", (row["id"],)
        ).fetchall(),
        "documents": con.execute(
            "SELECT id,filename,size,sha256 FROM documents WHERE transfer_id=%s ORDER BY created_at",
            (row["id"],),
        ).fetchall(),
    }


def event(con, row, action, actor, note):
    con.execute(
        "INSERT INTO events(chain_id,transfer_id,action,actor,note) VALUES (%s,%s,%s,%s,%s)",
        (row["chain_id"], row["id"], action, actor, note),
    )


def require_state(row, expected):
    if row["status"] != expected:
        raise Fault(409, "invalid_state", f"Trạng thái {row['status']} không cho phép thao tác này.")


def driver_valid(con, principal, username):
    row = con.execute(
        "SELECT username FROM drivers WHERE username=%s AND chain_id=%s", (username, principal.chain_id)
    ).fetchone()
    if not row:
        raise Fault(422, "invalid_driver", "Tài xế không thuộc chuỗi hoặc không tồn tại.")


def approve(con, principal, row, decision, note):
    principal.owner()
    require_state(row, "submitted")
    if row["created_by"] == principal.username:
        raise Fault(403, "self_approval", "Người tạo phiếu không được tự phê duyệt.")
    if decision == "approved":
        lot = con.execute("SELECT expires_on FROM lots WHERE id=%s FOR UPDATE", (row["lot_id"],)).fetchone()
        if lot["expires_on"] < date.today():
            raise Fault(409, "expired_lot", "Lô đã hết hạn; hãy từ chối để giải phóng giữ hàng.")
    else:
        con.execute("UPDATE lots SET reserved=reserved-%s WHERE id=%s", (row["quantity"], row["lot_id"]))
    con.execute("UPDATE transfers SET status=%s WHERE id=%s", (decision, row["id"]))
    event(con, row, decision, principal.username, note)
    advance_workflow(row, "approval", principal.username, note, approved=decision == "approved")


def dispatch(con, principal, row, driver):
    principal.owner()
    require_state(row, "approved")
    driver_valid(con, principal, driver)
    lot = con.execute("SELECT * FROM lots WHERE id=%s FOR UPDATE", (row["lot_id"],)).fetchone()
    if lot["expires_on"] < date.today():
        raise Fault(409, "expired_lot", "Không được xuất hàng đã hết hạn.")
    if lot["quantity"] < row["quantity"] or lot["reserved"] < row["quantity"]:
        raise Fault(409, "stock_conflict", "Tồn kho hoặc giữ hàng không đủ.")
    con.execute(
        "UPDATE lots SET quantity=quantity-%s,reserved=reserved-%s WHERE id=%s",
        (row["quantity"], row["quantity"], row["lot_id"]),
    )
    con.execute(
        "UPDATE transfers SET status='dispatched',driver_username=%s WHERE id=%s", (driver, row["id"])
    )
    event(con, row, "dispatched", principal.username, f"Giao tài xế {driver}")
    advance_workflow(row, "dispatch", principal.username, f"Giao tài xế {driver}")


def deliver(con, principal, row, actual, note):
    require_state(row, "dispatched")
    if principal.role != "driver" or row["driver_username"] != principal.username:
        raise Fault(403, "forbidden_driver", "Chỉ tài xế được phân công có thể xác nhận giao.")
    if actual > row["quantity"]:
        raise Fault(422, "invalid_quantity", "Số giao thực tế không được lớn hơn số xuất.")
    con.execute("UPDATE transfers SET status='delivered',actual_quantity=%s WHERE id=%s", (actual, row["id"]))
    shortage = row["quantity"] - actual
    event(con, row, "delivered", principal.username, f"Giao {actual}; thiếu {shortage}. {note}")
    advance_workflow(row, "delivery", principal.username, f"Giao {actual}; thiếu {shortage}. {note}")


def receive(con, principal, row, actual, note):
    require_state(row, "delivered")
    if principal.role != "store_manager" or principal.store_id != row["target_store_id"]:
        raise Fault(403, "forbidden_receiver", "Chỉ quản lý cửa hàng nhận được xác nhận nhập kho.")
    if actual > row["actual_quantity"]:
        raise Fault(422, "invalid_quantity", "Số nhận không được lớn hơn số tài xế báo giao.")
    lot = con.execute("SELECT * FROM lots WHERE id=%s FOR UPDATE", (row["lot_id"],)).fetchone()
    if actual and lot["expires_on"] < date.today():
        raise Fault(409, "expired_lot", "Hàng hết hạn: xác nhận nhận 0, ghi lý do; không nhập kho bán.")
    destination_lot = f"received-{row['id']}"
    if actual:
        con.execute(
            "INSERT INTO lots(id,chain_id,store_id,sku,name,quantity,expires_on,unit_cost_vnd) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                destination_lot,
                row["chain_id"],
                row["target_store_id"],
                lot["sku"],
                lot["name"],
                actual,
                lot["expires_on"],
                lot["unit_cost_vnd"],
            ),
        )
    con.execute(
        "UPDATE transfers SET status='received',received_quantity=%s WHERE id=%s", (actual, row["id"])
    )
    event(
        con,
        row,
        "received",
        principal.username,
        f"Nhận {actual}; chênh lệch với số xuất {row['quantity'] - actual}. {note}",
    )
    advance_workflow(row, "receipt", principal.username,
                     f"Nhận {actual}; chênh lệch với số xuất {row['quantity'] - actual}. {note}")
