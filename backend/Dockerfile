FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y wget gnupg ca-certificates curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install python dependencies
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --frozen --no-dev

# Install Playwright browsers
RUN /app/.venv/bin/playwright install --with-deps chromium firefox

# Copy app code
COPY . .

# Environment configuration
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

# Start server
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
