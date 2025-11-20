# Multi-stage Dockerfile for bintexttools
# Stage 1: Build stage
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy dependency files first for caching
COPY pyproject.toml uv.lock* README.md LICENSE ./

# Copy source code
COPY src/ ./src/

# Build the package (creates a wheel in dist/)
RUN uv build

# Stage 2: Runtime stage
FROM python:3.14-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/infra/web"

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the built wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the package from the wheel with web extras
# First install the wheel, then install the web extra dependencies
RUN WHEEL_FILE=$(ls /tmp/*.whl) && \
    pip install --no-cache-dir "$WHEEL_FILE" && \
    pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn[standard]>=0.32.0" "python-multipart>=0.0.12" "jinja2>=3.1.4"

# Copy web application source
COPY infra/web/app/ ./infra/web/app/

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for FastAPI
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI web application
WORKDIR /app/infra/web
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
