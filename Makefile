# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
SHELL := /bin/sh
COMPOSE ?= docker compose

.PHONY: up ai-up down logs verify demo-check release compose-config ui-check screenshots site site-check site-preview

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

screenshots:
	SCREENSHOT_DIR=dist/screenshots node scripts/ui-smoke.mjs

site:
	python3 scripts/build-site.py

site-check:
	node scripts/site-smoke.mjs

site-preview:
	python3 -m http.server 3181 --bind 127.0.0.1 --directory dist/site
