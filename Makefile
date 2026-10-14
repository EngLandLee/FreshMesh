# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
SHELL := /bin/sh
COMPOSE ?= docker compose

.PHONY: up down logs verify demo-check release compose-config

up:
	$(COMPOSE) up --build -d

ai-up:
	$(COMPOSE) -f compose.yaml -f compose.ai.yaml --profile ai up -d ollama
	$(COMPOSE) -f compose.yaml -f compose.ai.yaml --profile ai exec -T ollama ollama pull qwen2.5:0.5b
	$(COMPOSE) -f compose.yaml -f compose.ai.yaml --profile ai up -d api gateway portal

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

compose-config:
	$(COMPOSE) config --quiet

verify:
	./scripts/verify.sh

demo-check:
	python3 scripts/demo-check.py

release:
	./scripts/release.sh

ui-check:
	npm run test:ui
