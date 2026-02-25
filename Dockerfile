# ============================================================================
# Production Dockerfile for Churn Dashboard (Streamlit)
# Multi-stage build — expected size: ~500-600MB
# ============================================================================

# ---------- Stage 1: Build ----------
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    # Remove pip / setuptools / wheel — not needed at runtime
    pip uninstall -y pip setuptools wheel 2>/dev/null || true && \
    rm -rf /usr/local/lib/python3.11/site-packages/pip \
           /usr/local/lib/python3.11/site-packages/setuptools \
           /usr/local/lib/python3.11/site-packages/wheel \
           /usr/local/lib/python3.11/site-packages/pkg_resources \
           /usr/local/lib/python3.11/site-packages/jupyterlab_plotly 2>/dev/null || true

# Cleanup caches, tests, source files from installed packages
RUN SITE=/usr/local/lib/python3.11/site-packages && \
    find $SITE -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find $SITE -type d -name "tests"       -exec rm -rf {} + 2>/dev/null || true && \
    find $SITE -type d -name "test"        -exec rm -rf {} + 2>/dev/null || true && \
    find $SITE -type d -name "testing"     -exec rm -rf {} + 2>/dev/null || true && \
    find $SITE -type d -name "examples"    -exec rm -rf {} + 2>/dev/null || true && \
    find $SITE -name "*.pyc"  -delete 2>/dev/null || true && \
    find $SITE -name "*.pyo"  -delete 2>/dev/null || true && \
    find $SITE -name "*.c"    -delete 2>/dev/null || true && \
    find $SITE -name "*.cpp"  -delete 2>/dev/null || true && \
    find $SITE -name "*.h"    -delete 2>/dev/null || true && \
    find $SITE -name "*.so" -exec strip --strip-unneeded {} + 2>/dev/null || true && \
    find $SITE -path "*.dist-info/RECORD"  -delete 2>/dev/null || true && \
    find $SITE -path "*.dist-info/WHEEL"   -delete 2>/dev/null || true && \
    find $SITE -path "*.dist-info/LICENSE*" -delete 2>/dev/null || true && \
    # Trim pyarrow (134MB) — remove unused modules
    rm -rf $SITE/pyarrow/tests $SITE/pyarrow/gandiva \
           $SITE/pyarrow/dataset $SITE/pyarrow/orc \
           $SITE/pyarrow/flight $SITE/pyarrow/flight_sql \
           $SITE/pyarrow/acero $SITE/pyarrow/substrait \
           $SITE/pyarrow/_exec_plan* $SITE/pyarrow/_substrait* \
           $SITE/pyarrow/*parquet_encryption* 2>/dev/null || true && \
    # Trim pydeck mapbox data (14MB) — not needed for basic charts
    rm -rf $SITE/pydeck/nbextension $SITE/pydeck/static 2>/dev/null || true

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy only site-packages and streamlit binary from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/streamlit /usr/local/bin/streamlit

# Copy application code only (no .git, .env, etc — excluded by .dockerignore)
COPY app.py .

# Streamlit config — disable telemetry, set headless mode
RUN mkdir -p /app/.streamlit
RUN echo '[server]\nheadless = true\nport = 8501\naddress = "0.0.0.0"\nenableCORS = false\n\n[browser]\ngatherUsageStats = false' > /app/.streamlit/config.toml

EXPOSE 8501

# Health check using python (no curl needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py"]
