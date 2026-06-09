# ── Base ─────────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (pyVmomi & ldap need some libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies ─────────────────────────────────────────
FROM base AS deps

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ── Development ──────────────────────────────────────────
FROM deps AS development

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# ── Production ───────────────────────────────────────────
FROM deps AS production

COPY . .

# Create non-root user
RUN addgroup --system vcm && adduser --system --ingroup vcm vcm && \
    mkdir -p /app/uploads && chown -R vcm:vcm /app

USER vcm

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--proxy-headers", "--forwarded-allow-ips=*"]
