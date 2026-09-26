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
from app.domain.services.search_orchestrator import DealSearchOrchestrator, create_event
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


def get_clients(platform_names: list[str]) -> list[PlatformClient]:
    from app.platforms.factory import get_platform_client
    clients = []
    for p in platform_names:
        try:
            clients.append(get_platform_client(p))
        except Exception:
            pass
    return clients


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
    search_mode: str = Query("current_pincode", description="current_pincode or nearby_area"),
    radius_km: float = Query(10.0, description="Search radius in km"),
    expansion_strategy: str = Query("NEARBY_FIRST"),
    platforms: Optional[str] = Query(None, description="Comma-separated platforms"),
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
    plat_list = [p.strip() for p in platforms.split(",") if p.strip()] if platforms else []

    from fastapi import HTTPException
    if not plat_list:
        raise HTTPException(status_code=400, detail="No platform selected. Please select at least one platform.")

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
    
    if search_mode == "current_pincode":
        expansion_radii = []
    else:
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
            clients = get_clients(plat_list)
            if not clients:
                yield {"event": "search_error", "data": json.dumps({"message": "No valid platforms selected."})}
                return
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
                        if hasattr(event, "event"):
                            event._platform_name = client.platform_name
                        elif isinstance(event, dict):
                            event["_platform_name"] = client.platform_name
                        await queue.put(event)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    log.error(f"Error in orchestrator for {client.platform_name}: {e}", exc_info=True)
                    await queue.put(create_event({
                        "event": "platform_error", 
                        "search_id": search_id, 
                        "data": {"message": str(e), "platform": client.platform_name}
                    }))

            for c in clients:
                t = asyncio.create_task(_run_orch(c))
                active_tasks.append(t)

            async def _wait_and_close():
                await asyncio.gather(*active_tasks, return_exceptions=True)
                await queue.put(None) # EOF marker

            waiter = asyncio.create_task(_wait_and_close())

            completed_platforms = 0
            total_deals = 0
            
            while True:
                if cancel_event.is_set():
                    yield {"event": "search_cancelled", "data": json.dumps({"message": "Client disconnected"})}
                    break

                event = await queue.get()
                if event is None:
                    # All platforms finished
                    yield {"event": "search_completed", "data": json.dumps({"message": f"Scan completed across {len(clients)} platforms.", "total_deals": total_deals})}
                    break

                if hasattr(event, "model_dump"):
                    event_name = event.event
                    data = event.model_dump(exclude={"event", "search_id", "timestamp"})
                    if event_name == "deal_found" and "deal_data" in data:
                        data = data["deal_data"]
                else:
                    event_name = event.get("event", "message")
                    data = event.get("data", {})
                    
                if event_name == "search_completed":
                    completed_platforms += 1
                    total_deals += data.get("total_deals", 0)
                    # Don't emit individual platform completions to UI to avoid closing EventSource early
                    continue
                    
                if event_name == "search_error":
                    # Convert to platform_error so the frontend doesn't abort the entire scan
                    event_name = "platform_error"
                    data["platform"] = getattr(event, "_platform_name", "unknown") if not isinstance(event, dict) else event.get("_platform_name", "unknown")
                    
                yield {"event": event_name, "data": json.dumps(data)}

        except Exception as e:
            log.error("stream_search: unhandled exception in search_id=%s: %s", search_id, e, exc_info=True)
            yield {"event": "search_error", "data": json.dumps({"message": str(e)})}
        finally:
            watcher.cancel()
            if 'clients' in locals():
                for c in clients:
                    try:
                        await c.aclose()
                    except Exception as e:
                        log.error(f"Failed to close client {c.platform_name}: {e}")

    return EventSourceResponse(event_generator())
