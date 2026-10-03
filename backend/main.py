from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.routers import search, alerts, history, location, telegram, product_url, keywords, flash_price

import logging
from contextlib import asynccontextmanager
import asyncio
from app.scheduler import start_scheduler, stop_scheduler
from app.notifications.telegram_bot import start_telegram_bot_polling

logging.basicConfig(level=logging.INFO)
logging.getLogger("swiggy").setLevel(logging.INFO)
logging.getLogger("alert_runner").setLevel(logging.INFO)

_telegram_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.core.browser import BrowserManager
    from app.config import get_settings
    
    # Run Playwright Diagnostic
    settings = get_settings()
    logging.info("Diagnostics - Playwright enabled: %s", settings.playwright_enabled)
    if settings.playwright_enabled:
        try:
            await BrowserManager.ensure_started("chromium")
            logging.info("Diagnostics - Chromium: available")
            async with BrowserManager.get_page(browser_type="chromium") as page:
                logging.info("Diagnostics - Browser launch: successful")
        except Exception as e:
            logging.error("Diagnostics - Browser launch failed: %s", e)
    
    asyncio.create_task(BrowserManager.ensure_started())
    start_scheduler()
    global _telegram_task
    try:
        _telegram_task = asyncio.create_task(start_telegram_bot_polling())
    except Exception as e:
        logging.warning("Telegram bot polling failed to start (non-fatal): %s", e)
    yield
    # Shutdown
    if _telegram_task:
        _telegram_task.cancel()
        try:
            await _telegram_task
        except asyncio.CancelledError:
            pass
    stop_scheduler()
    await BrowserManager.close()

app = FastAPI(
    title="Worth-It API",
    description="Find the best Instamart deals across nearby dark stores.",
    version="1.0.0",
    lifespan=lifespan
)

from app.api import auth

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)}
    )

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(history.router, prefix="/api/history", tags=["Price History"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["Telegram"])
app.include_router(product_url.router, prefix="/api/product", tags=["Product URL"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["Keywords"])
app.include_router(flash_price.router, prefix="/api/flash-price", tags=["Flash Price"])

from app.config import get_settings

@app.get("/api/health")
def health_check():
    import os
    git_commit = os.environ.get("RENDER_GIT_COMMIT", "unknown")
    if git_commit == "unknown":
        # Try to get from local git if running locally
        try:
            import subprocess
            git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
        except Exception:
            pass
    return {
        "status": "ok", 
        "version": get_settings().app_version, 
        "git_commit": git_commit,
        "playwright_enabled": get_settings().playwright_enabled
    }

# Serve frontend static files if they exist (for unified Docker deployment)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# We look for a 'frontend/dist' folder relative to this file's parent directories
# In the unified Docker build, it will be placed at /app/frontend/dist
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        path_in_dist = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(path_in_dist):
            return FileResponse(path_in_dist)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
