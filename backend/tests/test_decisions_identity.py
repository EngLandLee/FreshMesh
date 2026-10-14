# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
from datetime import date, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from freshmesh_core.decisions import haversine, plan_route, recommend
from freshmesh_core.services import Fault, decode_identity


def lot(id, store, quantity, reserved=0, days=1):
    return {
        "id": id,
        "store_id": store,
        "sku": "RAU",
        "name": "Rau",
        "quantity": quantity,
        "reserved": reserved,
        "expires_on": date.today() + timedelta(days=days),
        "unit_cost_vnd": 10000,
    }


def test_recommendations_never_double_allocate_target_shortfall():
    stocks = [lot("a", "A", 100), lot("b", "B", 100), lot("c", "C", 0)]
    sales = [{"store_id": store, "sku": "RAU", "forecast": 10} for store in ["A", "B", "C"]]
    items = recommend(stocks, sales)["items"]
    transfers = [item for item in items if item["kind"] == "transfer"]
    assert sum(item["quantity"] for item in transfers if item["target_store_id"] == "C") == 20
    assert not any(item["target_store_id"] in {"A", "B"} for item in transfers)


def test_reserved_and_expired_stock_cannot_be_proposed():
    stocks = [lot("reserved", "A", 30, reserved=30), lot("expired", "A", 100, days=-1), lot("dest", "B", 0)]
    sales = [{"store_id": "A", "sku": "RAU", "forecast": 1}, {"store_id": "B", "sku": "RAU", "forecast": 10}]
    items = recommend(stocks, sales)["items"]
    assert all(item["kind"] != "transfer" for item in items)
    assert (
        next(
            item["quantity"]
            for item in items
            if item["kind"] == "purchase" and item["source_store_id"] == "B"
        )
        == 20
    )


def test_source_need_is_retained_and_vehicle_capacity_observed():
    stocks = [lot("a", "A", 100), lot("b", "B", 0)]
    sales = [{"store_id": "A", "sku": "RAU", "forecast": 8}, {"store_id": "B", "sku": "RAU", "forecast": 100}]
    items = recommend(stocks, sales)["items"]
    transfer = next(item for item in items if item["kind"] == "transfer")
    assert transfer["quantity"] == 40
    assert sum(item["quantity"] for item in items if item["source_store_id"] == "A") == 92


def test_route_returns_every_target_once_and_real_round_trip_distance():
    source = {"lat": 10.8, "lng": 106.7}
    targets = [
        {"store_id": str(i), "lat": 10.8, "lng": lng} for i, lng in enumerate([106.71, 106.72, 106.73])
    ]
    ordered, distance = plan_route(source, targets)
    assert {item["store_id"] for item in ordered} == {"0", "1", "2"}
    assert len(ordered) == 3
    assert distance == pytest.approx(2 * haversine(source, targets[-1]), abs=0.01)


def test_empty_route_is_explicit_error():
    with pytest.raises(Fault) as caught:
        plan_route({"lat": 0, "lng": 0}, [])
    assert caught.value.status == 422


@pytest.fixture
def signing(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://identity.example/realms/freshmesh")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = SimpleNamespace(get_signing_key_from_jwt=lambda _: SimpleNamespace(key=key.public_key()))
    import time

    claims = {
        "sub": "id",
        "preferred_username": "manager_a1",
        "exp": int(time.time()) + 60,
        "iat": int(time.time()),
        "iss": "https://identity.example/realms/freshmesh",
        "aud": "freshmesh-api",
        "chain_id": "CHAIN_A",
        "store_id": "A-01",
        "realm_access": {"roles": ["store_manager"]},
    }
    return key, client, claims


def test_real_signed_oidc_claims_preserve_scope(signing):
    key, client, claims = signing
    user = decode_identity(jwt.encode(claims, key, algorithm="RS256"), client)
    assert (user.role, user.chain_id, user.store_id) == ("store_manager", "CHAIN_A", "A-01")


@pytest.mark.parametrize(
    "field,value", [("aud", "other-api"), ("iss", "https://attacker.example"), ("exp", 1)]
)
def test_signed_wrong_audience_issuer_or_expired_tokens_are_rejected(signing, field, value):
    key, client, claims = signing
    claims[field] = value
    with pytest.raises(Fault) as caught:
        decode_identity(jwt.encode(claims, key, algorithm="RS256"), client)
    assert caught.value.status == 401


def test_tampered_signature_rejected(signing):
    key, client, claims = signing
    token = jwt.encode(claims, key, algorithm="RS256")
    parts = token.split(".")
    parts[1] = jwt.encode({**claims, "chain_id": "CHAIN_B"}, key, algorithm="RS256").split(".")[1]
    with pytest.raises(Fault) as caught:
        decode_identity(".".join(parts), client)
    assert caught.value.status == 401


@pytest.mark.parametrize(
    "update", [{"chain_id": "CHAIN_X"}, {"store_id": None}, {"realm_access": {"roles": ["owner", "driver"]}}]
)
def test_invalid_or_ambiguous_business_scope_denied(signing, update):
    key, client, claims = signing
    claims.update(update)
    with pytest.raises(Fault) as caught:
        decode_identity(jwt.encode(claims, key, algorithm="RS256"), client)
    assert caught.value.status == 403
