# ─────────────────────────────────────────────────────────────────────────────
# KnightLife API — production container
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
# so log lines appear immediately in `docker compose logs`
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── System dependencies ──────────────────────────────────────────────────────
# libpq-dev    → asyncpg C extension compilation
# tesseract-ocr → pytesseract shells out to this binary
# gcc          → required to compile C extensions during pip install
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──────────────────────────────────────────────────────
# Copy requirements first to leverage Docker layer caching —
# dependencies are re-installed only when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ─────────────────────────────────────────────────────────
COPY . .

EXPOSE 8000

# Run the FastAPI app via Uvicorn
# --host 0.0.0.0  → listen on all interfaces (required inside a container)
# --workers 2     → 2 worker processes (tune for production CPU count)
# --log-level info → match the application's logging.basicConfig level
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
