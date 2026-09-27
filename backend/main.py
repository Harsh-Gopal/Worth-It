from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.routers import search, alerts, history, location, telegram, product_url, keywords

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
    asyncio.create_task(BrowserManager.ensure_started())
    start_scheduler()
    global _telegram_task
    _telegram_task = asyncio.create_task(start_telegram_bot_polling())
    yield
    # Shutdown
    if _telegram_task:
        _telegram_task.cancel()
    stop_scheduler()
    await BrowserManager.close()

app = FastAPI(
    title="Worth-It API",
    description="Find the best Instamart deals across nearby dark stores.",
    version="1.0.0",
    lifespan=lifespan
)

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev
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

app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(history.router, prefix="/api/history", tags=["Price History"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["Telegram"])
app.include_router(product_url.router, prefix="/api/product", tags=["Product URL"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["Keywords"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
