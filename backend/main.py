from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.routers import search, alerts, history, location, telegram, product_url

from contextlib import asynccontextmanager
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

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

app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(history.router, prefix="/api/history", tags=["Price History"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["Telegram"])
app.include_router(product_url.router, prefix="/api/product", tags=["Product URL"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
