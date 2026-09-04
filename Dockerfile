# ==============================================================================
# SkyGuard AI - Production Multi-Stage Dockerfile
# Stage 1: Build React SPA Frontend
# Stage 2: Production Python Runtime (Serving API, WebSocket & Static UI)
# ==============================================================================

# --- Stage 1: Frontend Build ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Runtime ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime dependencies for PostgreSQL and numerical libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only wheel first to keep container image lightweight (~180MB vs 2.5GB CUDA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application backend, models, and launcher
COPY backend/ ./backend
COPY models/ ./models
COPY run.py ./

# Copy built frontend distribution from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create a non-privileged user for secure execution
RUN useradd -m -u 10001 skyguard && \
    chown -R skyguard:skyguard /app
USER skyguard

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    ENVIRONMENT=production

EXPOSE 8000

# Health check to ensure API readiness
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "run.py"]
