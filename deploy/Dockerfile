# ==============================================================================
# Axiom Production Multi-Stage Dockerfile
# Base: Python 3.13 Slim Debian Bookworm
# Security: Non-root user, minimal footprint, pinned production dependencies
# ==============================================================================

# Stage 1: Build & Dependencies
FROM python:3.13-slim-bookworm AS builder

WORKDIR /build

# Install compilation essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel & build tooling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies from pyproject.toml
COPY pyproject.toml README.md /build/
RUN pip install --no-cache-dir --prefix=/install .

# ==============================================================================
# Stage 2: Final Runtime Image
# ==============================================================================
FROM python:3.13-slim-bookworm AS runtime

LABEL maintainer="Axiom Engineering Team <engineering@axiom.ai>"
LABEL description="Axiom: Production Zero-Hallucination Agentic RAG Platform"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/app/src:${PYTHONPATH}"

# Install minimal runtime libraries (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN groupadd -g 1000 axiom && \
    useradd -u 1000 -g axiom -s /bin/bash -m axiom

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /install

# Copy application source and evals
COPY --chown=axiom:axiom src/ /app/src/
COPY --chown=axiom:axiom evals/ /app/evals/
COPY --chown=axiom:axiom pyproject.toml README.md /app/

# Switch to unprivileged user
USER axiom

# Expose FastAPI Gateway HTTP Port
EXPOSE 8000

# Docker Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Production ASGI Server
CMD ["python", "-m", "uvicorn", "axiom.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
