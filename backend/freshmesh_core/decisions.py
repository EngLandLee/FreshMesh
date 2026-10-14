# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Small, explainable decisions based on demo sales, not claimed ML accuracy."""

import math
from collections import defaultdict
from datetime import date

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from freshmesh_core.services import Fault

PROVENANCE = "Dữ liệu demo tự tạo; không phải giao dịch thực. Trung bình bán 7 ngày, không dùng FL."
ASSUMPTIONS = [
    "Nhu cầu dự kiến bằng trung bình bán 7 ngày, chưa đánh giá trên giao dịch thực.",
    "Hạn dùng tính theo ngày; đề xuất không thay thế kiểm tra chất lượng thực phẩm.",
    "Điều chuyển nội bộ trong cùng chuỗi; không chia sẻ dữ liệu giữa các chuỗi.",
]


def recommend(lots, sales, today=None):
    today = today or date.today()
    forecasts = {(row["store_id"], row["sku"]): float(row["forecast"]) for row in sales}
    stock = defaultdict(int)
    for lot in lots:
        if lot["expires_on"] >= today:
            stock[(lot["store_id"], lot["sku"])] += lot["quantity"] - lot["reserved"]
    deficits = {key: max(0, math.ceil(value * 2) - stock[key]) for key, value in forecasts.items()}
    items = []
    # Allocate each target deficit once; multiple source lots cannot double-promise replenishment.
    for lot in sorted(lots, key=lambda row: (row["expires_on"], row["id"])):
        remaining = (lot["expires_on"] - today).days
        if remaining < 0:
            continue
        available = lot["quantity"] - lot["reserved"]
        own_need = math.ceil(forecasts.get((lot["store_id"], lot["sku"]), 0) * max(1, remaining))
        surplus = max(0, available - own_need)
        for (target, sku), need in sorted(deficits.items()):
            if sku != lot["sku"] or target == lot["store_id"] or need <= 0 or surplus <= 0:
                continue
            quantity = min(surplus, need, 40)
            items.append(
                {
                    "kind": "transfer",
                    "source_store_id": lot["store_id"],
                    "target_store_id": target,
                    "lot_id": lot["id"],
                    "sku": sku,
                    "name": lot["name"],
                    "quantity": quantity,
                    "forecast_units": forecasts[(target, sku)],
                    "reason": f"Dư {surplus} gói trước hạn; cửa hàng nhận thiếu {need} gói cho 2 ngày.",
                    "estimated_value_vnd": quantity * lot["unit_cost_vnd"],
                    "provenance": PROVENANCE,
                }
            )
            deficits[(target, sku)] -= quantity
            surplus -= quantity
        if remaining <= 2 and surplus > 0:
            items.append(
                {
                    "kind": "markdown",
                    "source_store_id": lot["store_id"],
                    "target_store_id": None,
                    "lot_id": lot["id"],
                    "sku": lot["sku"],
                    "name": lot["name"],
                    "quantity": surplus,
                    "forecast_units": forecasts.get((lot["store_id"], lot["sku"]), 0),
                    "reason": "Còn dư trước hạn sau phân bổ điều chuyển; cân nhắc giảm giá, "
                    "không tự áp dụng giá và không coi giá trị tồn là lợi ích đã đạt.",
                    "estimated_value_vnd": surplus * lot["unit_cost_vnd"],
                    "provenance": PROVENANCE,
                }
            )
    for (store, sku), need in sorted(deficits.items()):
        if need > 0:
            items.append(
                {
                    "kind": "purchase",
                    "source_store_id": store,
                    "target_store_id": None,
                    "lot_id": None,
                    "sku": sku,
                    "name": sku,
                    "quantity": need,
                    "forecast_units": forecasts[(store, sku)],
                    "reason": "Thiếu cho 2 ngày sau các đề xuất điều chuyển; cần người phụ trách "
                    "xem xét nhập, không tạo đơn nhà cung cấp.",
                    "estimated_value_vnd": None,
                    "provenance": PROVENANCE,
                }
            )
    return {
        "items": items,
        "method": "Trung bình bán 7 ngày + phân bổ dư/thiếu theo hạn dùng",
        "assumptions": ASSUMPTIONS,
    }


def haversine(a, b):
    lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
    dlat = lat2 - lat1
    dlng = math.radians(b["lng"] - a["lng"])
    v = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(v)))


def plan_route(source, targets):
    if not targets:
        raise Fault(422, "empty_route", "Tuyến giao phải có điểm nhận.")
    points = [source, *targets]
    matrix = [[round(haversine(a, b) * 1000) for b in points] for a in points]
    manager = pywrapcp.RoutingIndexManager(len(points), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance(i, j):
        return matrix[manager.IndexToNode(i)][manager.IndexToNode(j)]

    callback = routing.RegisterTransitCallback(distance)
    routing.SetArcCostEvaluatorOfAllVehicles(callback)
    settings = pywrapcp.DefaultRoutingSearchParameters()
    settings.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    settings.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    settings.time_limit.seconds = 1
    solution = routing.SolveWithParameters(settings)
    if solution is None:
        raise Fault(503, "routing_unavailable", "Solver không tìm được tuyến hợp lệ.")
    ordered, metres, index = [], 0, routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node:
            ordered.append(points[node])
        next_index = solution.Value(routing.NextVar(index))
        metres += routing.GetArcCostForVehicle(index, next_index, 0)
        index = next_index
    return ordered, round(metres / 1000, 3)
