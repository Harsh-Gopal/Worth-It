# Troubleshooting Guide

This guide helps resolve common issues encountered while installing, running, or developing Worth-It.

## Docker Issues

### 1. "Docker is not running" or "Cannot connect to the Docker daemon"
**Cause:** The Docker daemon is not active on your system or you lack permissions.
**Solution:**
- **macOS/Windows:** Open the Docker Desktop application manually from your Applications/Start menu. Wait for the engine to initialize, then run the installer again.
- **Linux:** Start the daemon with `sudo systemctl start docker` and ensure your user is added to the `docker` group (`sudo usermod -aG docker $USER`).

### 2. "Port 8000 is already in use" or "Bind for 0.0.0.0:3000 failed"
**Cause:** Another application (or an orphaned Worth-It container) is already using the port required by the frontend (3000) or backend (8000).
**Solution:**
- Run `docker compose down` to clean up any orphaned containers.
- Identify what is using the port: `lsof -i :3000` or `lsof -i :8000`.
- Stop the conflicting application and restart Worth-It.

## Application Issues

### 3. Backend fails health check during startup
**Cause:** The Python FastAPI backend failed to start inside the container, likely due to a missing dependency, port conflict, or syntax error in a recent configuration change.
**Solution:**
- Check the logs: `docker compose logs backend`
- If you see dependency errors, try rebuilding the images: `docker compose build --no-cache`

### 4. Platform returns "Technical Error" in the Live Console
**Cause:** The backend orchestrator failed to resolve a store or execute a search for a specific platform due to a WAF (Web Application Firewall) block, a change in the platform's API schema, or an IP ban.
**Solution:**
- This is normal behavior when quick-commerce platforms deploy aggressive anti-bot protections.
- Wait for a cooldown period (e.g. 1 hour).
- Because of Worth-It's isolated architecture, the remaining platforms (e.g. Swiggy) will continue to scan normally.

### 5. Platform returns "Not Available at Location"
**Cause:** The latitude and longitude you provided in the configuration map to a location that the specific platform does not service (e.g. Zepto is not present in that city).
**Solution:**
- This is expected. Worth-It will ignore this platform for this specific scan and proceed with others.

### 6. Live Console shows no data / Disconnected
**Cause:** The Server-Sent Events (SSE) connection between the React frontend and FastAPI backend dropped, often caused by a proxy timeout.
**Solution:**
- The frontend will attempt to auto-reconnect.
- Ensure your NGINX or reverse proxy configuration is configured to allow long-lived HTTP connections (see `DEPLOYMENT.md`).

## Development Issues

### 7. Playwright errors ("Browser closed unexpectedly")
**Cause:** A platform adapter utilizing Playwright crashed.
**Solution:**
- Ensure the Docker image was built successfully (`Playwright install` is run as part of the `Dockerfile`).
- Do not attempt to rely on your host machine's local Chrome installation. All Playwright execution must happen headless within the container environment.
