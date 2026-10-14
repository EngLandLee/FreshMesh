# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
FROM ghcr.io/astral-sh/uv:0.9.17-python3.12-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY freshmesh_core ./freshmesh_core
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/freshmesh_core /app/freshmesh_core
RUN useradd --create-home --uid 10001 freshmesh \
 && chown -R freshmesh:freshmesh /app
USER 10001
EXPOSE 8100
CMD ["uvicorn", "freshmesh_core.main:app", "--host", "0.0.0.0", "--port", "8100"]
