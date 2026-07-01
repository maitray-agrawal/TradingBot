# ─────────────────────────────────────────────────────────────────────────────
# PrimeTrade AI — Multi-stage Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 : builder   — installs all Python dependencies
# Stage 2 : runtime   — lean production image with only required files
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# System build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user early
RUN groupadd --gid 1001 primetrade \
    && useradd --uid 1001 --gid primetrade --shell /bin/bash --create-home primetrade

WORKDIR /build

# Copy and install dependencies into an isolated prefix
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="PrimeTrade AI <noreply@primetrade.ai>"
LABEL org.opencontainers.image.title="PrimeTrade AI"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.description="Sentiment-Driven Crypto Trading Analytics & Binance Futures Testnet Bot"
LABEL org.opencontainers.image.licenses="MIT"

# Minimal runtime system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --gid 1001 primetrade \
    && useradd --uid 1001 --gid primetrade --shell /bin/bash --create-home primetrade

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy project source (filtered by .dockerignore)
COPY --chown=primetrade:primetrade . .

# Create required runtime directories
RUN mkdir -p \
        data/raw \
        data/processed \
        data/uploads \
        data/exports \
        logs \
        analytics/outputs/charts \
        analytics/outputs/reports \
        analytics/outputs/strategy \
        analytics/reports/generated \
    && chown -R primetrade:primetrade /app

# Switch to non-root user
USER primetrade

# Streamlit configuration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Health check — verify Streamlit is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

# Default: launch Streamlit dashboard
CMD ["python", "-m", "streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
