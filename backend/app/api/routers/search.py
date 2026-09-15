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
from app.persistence.repositories.price_history_repo import PriceHistoryRepository
from app.domain.services.price_history_service import PriceHistoryService
from app.config import get_settings

router = APIRouter()

MAX_RADIUS_KM = 20.0  # Absolute system limit — enforced server-side


# ─── Dependencies ─────────────────────────────────────────────────────────────

def get_db():
    return Database(get_settings().database_path)


def get_store_cache():
    return StoreCache(get_settings().store_cache_path)


def get_http_client():
    client = httpx.Client(timeout=15.0)
    try:
        yield client
    finally:
        client.close()


def get_price_history(db: Database = Depends(get_db)):
    repo = PriceHistoryRepository(db)
    return PriceHistoryService(repo)


# ─── SSE Event Stream ─────────────────────────────────────────────────────────

@router.get("/stream")
async def stream_search(
    request: Request,
    # Search targets
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    keywords: Optional[str] = Query(None, description="Comma-separated keywords"),
    exclude_keywords: Optional[str] = Query(None, description="Comma-separated exclude keywords"),
    product_urls: Optional[str] = Query(None, description="Comma-separated Instamart product URLs"),
    # Deal conditions
    min_discount_pct: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_price_drop_pct: Optional[float] = Query(None),
    require_historical_low: bool = Query(False),
    require_in_stock: bool = Query(True),
    condition_operator: str = Query("AND"),
    # Geographic
    radius_km: float = Query(10.0),
    expansion_strategy: str = Query("NEARBY_FIRST"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    local_store_id: Optional[str] = Query(None),
    # Deps
    client: httpx.Client = Depends(get_http_client),
    store_cache: StoreCache = Depends(get_store_cache),
    price_history: PriceHistoryService = Depends(get_price_history),
):
    """
    Stream deal search progress via Server-Sent Events.
    
    The client closes the connection to cancel. The server detects disconnection
    and stops further geographic expansion.
    """
    settings = get_settings()

    # Resolve defaults
    _lat = lat if lat is not None else settings.center_lat
    _lng = lng if lng is not None else settings.center_lng
    _store_id = local_store_id if local_store_id is not None else settings.local_store_id

    # Parse comma-separated lists
    cat_list = [c.strip() for c in categories.split(",")] if categories else []
    kw_list = [k.strip() for k in keywords.split(",")] if keywords else []
    ex_list = [e.strip() for e in exclude_keywords.split(",")] if exclude_keywords else []
    url_list = [u.strip() for u in product_urls.split(",")] if product_urls else []

    # 20km server-side clamp
    _radius = min(radius_km, MAX_RADIUS_KM)

    condition = DealCondition(
        min_discount_pct=min_discount_pct,
        max_price=max_price,
        price_drop_pct=min_price_drop_pct,
        require_historical_low=require_historical_low,
        require_in_stock=require_in_stock,
        condition_operator=condition_operator,
    )

    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=_lat,
        center_lng=_lng,
        local_store_id=_store_id,
        price_history_service=price_history,
    )

    search_id = str(uuid.uuid4())
    cancel_event = asyncio.Event()

    # Determine expansion radii
    expansion_radii = [3.0, 5.0, _radius]
    # Deduplicate and clamp
    expansion_radii = list(dict.fromkeys(min(r, MAX_RADIUS_KM) for r in expansion_radii))

    async def event_generator():
        try:
            if url_list:
                # URL/wishlist mode
                gen = orchestrator.run_url_search(
                    search_id=search_id,
                    product_urls=url_list,
                    condition=condition,
                    expansion_radii_km=expansion_radii,
                    strategy=expansion_strategy,
                    cancel_event=cancel_event,
                )
            else:
                # Keyword/category mode
                search_query = " ".join(kw for kw in (cat_list + kw_list) if kw)
                gen = orchestrator.run_search(
                    search_id=search_id,
                    keyword=search_query,
                    match_keywords=kw_list if kw_list else None,
                    exclude_keywords=ex_list if ex_list else None,
                    condition=condition,
                    expansion_radii_km=expansion_radii,
                    strategy=expansion_strategy,
                    cancel_event=cancel_event,
                )

            async for event_dict in gen:
                if await request.is_disconnected():
                    cancel_event.set()
                    break
                yield {
                    "event": event_dict["event"],
                    "data": json.dumps(event_dict["data"]),
                }

        except asyncio.CancelledError:
            cancel_event.set()
            yield {
                "event": "search_cancelled",
                "data": json.dumps({"message": "Search cancelled by client disconnect"}),
            }
        except Exception as e:
            yield {
                "event": "search_error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(event_generator())
