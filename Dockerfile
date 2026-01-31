# =============================================================================
# Multi-stage Dockerfile for Django + Vite + Docs
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build frontend assets (Vite + React)
# -----------------------------------------------------------------------------
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Build documentation (Astro/Starlight)
# -----------------------------------------------------------------------------
FROM node:22-alpine AS docs-builder

WORKDIR /app/docs
COPY docs/package*.json ./
RUN npm ci
COPY docs/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Python production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY manage.py ./
COPY fengshui/ ./fengshui/
COPY bazi/ ./bazi/
COPY locale/ ./locale/
COPY theme/ ./theme/ 2>/dev/null || true

# Copy built frontend assets
COPY --from=frontend-builder /app/static ./static

# Copy built docs to serve as static files (optional)
COPY --from=docs-builder /app/docs/dist ./static/docs

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "fengshui.wsgi:application"]
