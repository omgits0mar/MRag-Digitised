# syntax=docker/dockerfile:1.7

# -----------------------------------------------------------------------------
# Stage 1 — builder: install Python dependencies into an isolated prefix so the
# runtime image never needs gcc, g++, or build headers.
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --prefix=/install .

# -----------------------------------------------------------------------------
# Stage 2 — runtime: slim image with only the installed packages, the source
# tree, and prompt templates. No corpus, no model cache, no build tools.
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HF_HOME=/hf-cache \
    TRANSFORMERS_CACHE=/hf-cache \
    DATA_DIR=/data \
    UPLOAD_DIR=/data/uploads

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system mrag \
    && useradd --system --gid mrag --home /app --shell /usr/sbin/nologin mrag

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src ./src
COPY prompts ./prompts
COPY .env.example ./.env.example

RUN mkdir -p /data /data/uploads /data/processed /data/db /hf-cache \
    && chown -R mrag:mrag /app /data /hf-cache

USER mrag

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "mrag.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
