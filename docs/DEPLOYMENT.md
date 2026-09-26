# Deployment Guide

Worth-It is packaged using Docker and Docker Compose to ensure a reproducible, reliable runtime environment. This completely eliminates the need for manual configuration of Python, Node, or Playwright browser dependencies.

## Architecture

The production/deployed architecture consists of:
- **Frontend Container (`worthit-frontend`)**: An NGINX alpine container serving the compiled static React SPA and proxying `/api/` traffic.
- **Backend Container (`worthit-backend`)**: A Python 3.12 container running FastAPI via `uvicorn`. The container comes pre-installed with Playwright dependencies.
- **Data Volume (`worth-it-data`)**: A persistent Docker volume mapped to `/app/data` inside the backend. It stores the local SQLite database (`local_stores.db` or similar).

## Deployment

### Locally via Installers (One-Click)
For local macOS, Windows, or Linux usage, simply double-click the respective `Worth-It Install` script to build the images, then use the `Worth-It` daily launcher to run the stack.

### Cloud/VPS Deployment
To deploy Worth-It to a cloud provider (e.g. DigitalOcean, AWS EC2, or Hetzner):

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Worth-It.git
   cd Worth-It
   ```

2. **Configure Environment Variables**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env to include your TELEGRAM_BOT_TOKEN or other secrets
   ```

3. **Start the Stack**:
   ```bash
   docker compose up -d --build
   ```

4. **Reverse Proxy (HTTPS)**:
   It is highly recommended to place a reverse proxy like Caddy, Traefik, or an edge NGINX server in front of port `3000` to handle SSL/TLS termination. Ensure your proxy configuration forwards headers properly and allows long-lived connections for Server-Sent Events (SSE).

## Data Persistence & Backups
All critical data (settings, alerts, price history, store cache) is stored in the Docker volume. 
To back up your data:
```bash
docker run --rm -v worth-it-data:/data -v $(pwd):/backup alpine tar cvzf /backup/worthit_backup.tar.gz /data
```
