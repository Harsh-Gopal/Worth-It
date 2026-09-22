"""
Search router — SSE streaming endpoint for deal searches.

Supports three search modes:
  1. Keyword/category search (default)
  2. Exact product URL search  
  3. Wishlist: multiple product URLs searched simultaneously

All modes use the same geographic expansion engine.
"""
import asyncio
import uuid
import json
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.domain.models.deal import DealCondition
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.persistence.database import Database
from app.geo.store_cache import StoreCache
from app.platforms.swiggy import SwiggyClient
from app.platforms.zepto import ZeptoClient
from app.platforms.blinkit import BlinkitClient
from app.platforms.base import PlatformClient
from app.persistence.repositories.price_history_repo import PriceHistoryRepository
from app.domain.services.price_history_service import PriceHistoryService
from app.persistence.repositories.alert_repo import AlertRepository
from app.domain.services.alert_engine import AlertEngine
from app.domain.models.alert import AlertRule
from datetime import datetime, timezone
from app.config import get_settings
import logging

log = logging.getLogger("search_router")

router = APIRouter()

MAX_RADIUS_KM = 20.0  # Absolute system limit — enforced server-side


# ─── Dependencies ─────────────────────────────────────────────────────────────

def get_db():
    return Database(get_settings().database_path)


def get_store_cache():
    from app.geo.store_cache import get_global_cache
    return get_global_cache(get_settings().store_cache_path)


def get_clients() -> list[PlatformClient]:
    return [SwiggyClient(), ZeptoClient(), BlinkitClient()]


def get_price_history(db: Database = Depends(get_db)):
    repo = PriceHistoryRepository(db)
    return PriceHistoryService(repo)


# ─── SSE Stream Endpoint ───────────────────────────────────────────────────────

@router.get("/stream")
async def stream_search(
    request: Request,
    # Search targets
    keywords: Optional[str] = Query(None, description="Comma-separated keywords"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    exclude_keywords: Optional[str] = Query(None, description="Comma-separated exclusions"),
    product_urls: Optional[str] = Query(None, description="Comma-separated product URLs"),
    # Deal conditions
    max_price: Optional[float] = Query(None),
    min_price_drop_pct: Optional[float] = Query(None),
    require_historical_low: bool = Query(False),
    condition_operator: str = Query("AND"),
    # Location
    lat: Optional[float] = Query(None, description="User latitude"),
    lng: Optional[float] = Query(None, description="User longitude"),
    local_store_id: Optional[str] = Query(None, description="Known local Instamart store ID"),
    # Expansion
    radius_km: float = Query(10.0, description="Search radius in km"),
    expansion_strategy: str = Query("NEARBY_FIRST"),
    store_cache: StoreCache = Depends(get_store_cache),
    price_history: PriceHistoryService = Depends(get_price_history),
):
    """SSE stream for keyword/category deal searches."""
    settings = get_settings()

    # Parse inputs
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
    cat_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else []
    excl_list = [e.strip() for e in exclude_keywords.split(",") if e.strip()] if exclude_keywords else []
    url_list = [u.strip() for u in product_urls.split(",") if u.strip()] if product_urls else []

    all_targets = cat_list + kw_list
    if not all_targets and not url_list:
        async def _error():
            yield {"event": "search_error", "data": json.dumps({"message": "No keywords, categories, or product URLs provided."})}
        return EventSourceResponse(_error())

    effective_lat = lat if lat is not None else settings.center_lat
    effective_lng = lng if lng is not None else settings.center_lng
    effective_store_id = local_store_id or settings.local_store_id

    condition = DealCondition(
        max_price=max_price,
        price_drop_pct=min_price_drop_pct,
        require_historical_low=require_historical_low,
        condition_operator=condition_operator,
        require_in_stock=True,
    )

    search_id = str(uuid.uuid4())
    radius_clamped = min(radius_km, MAX_RADIUS_KM)
    expansion_radii = [3.0, 5.0, radius_clamped]
    expansion_radii = list(dict.fromkeys(min(r, MAX_RADIUS_KM) for r in expansion_radii))

    log.info(
        "stream_search: id=%s lat=%.4f lng=%.4f store=%s keywords=%s cats=%s urls=%d",
        search_id, effective_lat, effective_lng, effective_store_id,
        kw_list, cat_list, len(url_list),
    )

    async def event_generator():
        cancel_event = asyncio.Event()

        # Watch for client disconnect
        async def _watch_disconnect():
            try:
                while True:
                    if await request.is_disconnected():
                        cancel_event.set()
                        return
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass

        watcher = asyncio.create_task(_watch_disconnect())

        try:
            clients = get_clients()
            queue = asyncio.Queue()
            active_tasks = []

            async def _run_orch(client):
                try:
                    orchestrator = DealSearchOrchestrator(
                        client=client,
                        store_cache=store_cache,
                        center_lat=effective_lat,
                        center_lng=effective_lng,
                        local_store_id=effective_store_id if client.platform_name == "swiggy" else None,
                        price_history_service=price_history,
                    )
                    async for event in orchestrator.run_combined_search(
                        search_id=search_id,
                        keyword=" ".join(all_targets) if all_targets else "",
                        product_urls=url_list,
                        match_keywords=all_targets if all_targets else None,
                        exclude_keywords=excl_list or None,
                        condition=condition,
                        expansion_radii_km=expansion_radii,
                        strategy=expansion_strategy,
                        cancel_event=cancel_event,
                    ):
                        await queue.put(event)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    log.error(f"Error in orchestrator for {client.platform_name}: {e}")

            for c in clients:
                t = asyncio.create_task(_run_orch(c))
                active_tasks.append(t)

            async def _wait_and_close():
                await asyncio.gather(*active_tasks, return_exceptions=True)
                await queue.put(None) # EOF marker

            waiter = asyncio.create_task(_wait_and_close())

            while True:
                if cancel_event.is_set():
                    yield {"event": "search_cancelled", "data": json.dumps({"message": "Client disconnected"})}
                    break

                event = await queue.get()
                if event is None:
                    break

                event_name = event.get("event", "message")
                data = event.get("data", {})
                yield {"event": event_name, "data": json.dumps(data)}

        except Exception as e:
            log.error("stream_search: unhandled exception in search_id=%s: %s", search_id, e, exc_info=True)
            yield {"event": "search_error", "data": json.dumps({"message": str(e)})}
        finally:
            watcher.cancel()

    return EventSourceResponse(event_generator())
