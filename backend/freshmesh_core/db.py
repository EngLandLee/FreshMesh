# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
"""Managed structured data; SQL transactions protect stock and reservation invariants."""

import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

SCHEMA = """
CREATE TABLE IF NOT EXISTS stores (
 id text PRIMARY KEY, chain_id text NOT NULL, name text NOT NULL, lat double precision NOT NULL,
 lng double precision NOT NULL, UNIQUE(id,chain_id));
CREATE TABLE IF NOT EXISTS lots (
 id text PRIMARY KEY, chain_id text NOT NULL, store_id text NOT NULL, sku text NOT NULL,
 name text NOT NULL, quantity integer NOT NULL CHECK(quantity >= 0),
 reserved integer NOT NULL DEFAULT 0 CHECK(reserved >= 0 AND reserved <= quantity),
 expires_on date NOT NULL, unit_cost_vnd integer NOT NULL CHECK(unit_cost_vnd > 0),
 FOREIGN KEY(store_id,chain_id) REFERENCES stores(id,chain_id));
CREATE TABLE IF NOT EXISTS sales (
 chain_id text NOT NULL, store_id text NOT NULL, sku text NOT NULL, day date NOT NULL,
 quantity integer NOT NULL CHECK(quantity>=0), PRIMARY KEY(store_id,sku,day),
 FOREIGN KEY(store_id,chain_id) REFERENCES stores(id,chain_id));
CREATE TABLE IF NOT EXISTS drivers (
 username text PRIMARY KEY, chain_id text NOT NULL, name text NOT NULL);
CREATE TABLE IF NOT EXISTS transfers (
 id uuid PRIMARY KEY, chain_id text NOT NULL, source_store_id text NOT NULL, target_store_id text NOT NULL,
 lot_id text NOT NULL REFERENCES lots(id), quantity integer NOT NULL CHECK(quantity > 0),
 status text NOT NULL CHECK(status IN ('submitted','approved','rejected','dispatched','delivered','received')),
 created_by text NOT NULL, driver_username text REFERENCES drivers(username),
 actual_quantity integer CHECK(actual_quantity>=0 AND actual_quantity<=quantity),
 received_quantity integer CHECK(received_quantity>=0 AND received_quantity<=actual_quantity),
 note text NOT NULL DEFAULT '', process_id text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(source_store_id<>target_store_id),
 FOREIGN KEY(source_store_id,chain_id) REFERENCES stores(id,chain_id),
 FOREIGN KEY(target_store_id,chain_id) REFERENCES stores(id,chain_id));
CREATE TABLE IF NOT EXISTS events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, chain_id text NOT NULL,
 transfer_id uuid NOT NULL REFERENCES transfers(id), action text NOT NULL, actor text NOT NULL,
 note text NOT NULL DEFAULT '', at timestamptz NOT NULL DEFAULT now(), UNIQUE(transfer_id,action));
CREATE TABLE IF NOT EXISTS documents (
 id uuid PRIMARY KEY, chain_id text NOT NULL, transfer_id uuid NOT NULL REFERENCES transfers(id),
 filename text NOT NULL, object_key text NOT NULL UNIQUE, size integer NOT NULL CHECK(size>0),
 sha256 text NOT NULL, created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS routes (
 id uuid PRIMARY KEY, chain_id text NOT NULL, driver_username text NOT NULL REFERENCES drivers(username),
 status text NOT NULL DEFAULT 'planned' CHECK(status IN ('planned','dispatched')),
 transfer_ids uuid[] NOT NULL, stops jsonb NOT NULL, distance_km double precision NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS transfer_chain ON transfers(chain_id,status);
CREATE INDEX IF NOT EXISTS document_transfer ON documents(transfer_id);
CREATE OR REPLACE FUNCTION prevent_event_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Audit events are append-only'; END; $$;
DROP TRIGGER IF EXISTS immutable_events ON events;
CREATE TRIGGER immutable_events BEFORE UPDATE OR DELETE ON events
FOR EACH ROW EXECUTE FUNCTION prevent_event_mutation();
"""


@contextmanager
def connect():
    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=5) as con:
        yield con


def initialize():
    with connect() as con:
        con.execute(SCHEMA)
        if con.execute("SELECT count(*) AS n FROM stores").fetchone()["n"]:
            return
        stores = [
            ("A-01", "CHAIN_A", "Mini-mart Bình Thạnh", 10.810, 106.709),
            ("A-02", "CHAIN_A", "Mini-mart Phú Nhuận", 10.800, 106.680),
            ("A-03", "CHAIN_A", "Mini-mart Tân Bình", 10.801, 106.651),
            ("B-01", "CHAIN_B", "Chuỗi B — Quận 7", 10.735, 106.720),
        ]
        for store in stores:
            con.execute("INSERT INTO stores VALUES (%s,%s,%s,%s,%s)", store)
        for chain, store, qty, days in [
            ("CHAIN_A", "A-01", 100, 2),
            ("CHAIN_A", "A-02", 5, 5),
            ("CHAIN_A", "A-03", 3, 5),
            ("CHAIN_B", "B-01", 60, 3),
        ]:
            con.execute(
                "INSERT INTO lots(id,chain_id,store_id,sku,name,quantity,expires_on,unit_cost_vnd) "
                "VALUES (%s,%s,%s,'RAU-01','Rau cải — gói 500g',%s,current_date+%s,15000)",
                (f"{store}-RAU-01", chain, store, qty, days),
            )
            daily = 8 if store == "A-01" else 20
            for day in range(1, 8):
                con.execute(
                    "INSERT INTO sales VALUES (%s,%s,%s,current_date-%s,%s)",
                    (chain, store, "RAU-01", day, daily + (day % 3) - 1),
                )
        con.execute(
            "INSERT INTO drivers VALUES ('driver_a','CHAIN_A','Tài xế chuỗi A'),"
            "('driver_b','CHAIN_B','Tài xế chuỗi B')"
        )
