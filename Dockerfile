# Stage 1: Build the Vite frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the FastAPI backend + Playwright dependencies
FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y wget gnupg ca-certificates curl && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package resolution
COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /uvx /bin/

WORKDIR /app/backend

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install python dependencies using uv
ENV UV_PROJECT_ENVIRONMENT=/app/backend/.venv
RUN uv sync --frozen --no-dev

# Install Playwright browsers (chromium, firefox)
RUN /app/backend/.venv/bin/playwright install --with-deps chromium firefox

# Copy the rest of the backend code
COPY backend/ ./

# Copy the built frontend from Stage 1 so FastAPI can serve it
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Environment configuration
ENV PYTHONPATH=/app/backend
# By default we bind to 8000 if PORT is not set (Render provides $PORT)
ENV PORT=8000
ENV HOST=0.0.0.0

# Start server using bash to properly expand $PORT variable provided by Render
# main:app tells uvicorn to look for main.py in the current WORKDIR (/app/backend)
CMD ["sh", "-c", "/app/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
