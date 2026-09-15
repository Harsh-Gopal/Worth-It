"""
URL-based product lookup router.

Allows a user to paste a specific Instamart product URL and check:
  - Is the product available?
  - Does it qualify as a deal at the resolved location?
  - Can we find it in nearby stores?

URL format supported:
  https://www.swiggy.com/instamart/item/<product_id>
  https://www.swiggy.com/instamart/item/<product_id>?itemId=<id>
"""
import re
import httpx
import asyncio
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from app.platforms.instamart.client import product_at_store
from app.api.routers.search import get_db, get_store_cache, get_price_history, get_http_client
from app.domain.models.deal import DealCondition
from app.geo.store_cache import StoreCache
from app.domain.services.price_history_service import PriceHistoryService
from app.persistence.database import Database
from app.config import get_settings

log = logging.getLogger("product_url_router")
router = APIRouter()

# Extract product ID from Instamart URLs
_ITEM_ID_RE = re.compile(r"/instamart/item/(\d+)", re.IGNORECASE)
_ITEM_PARAM_RE = re.compile(r"[?&]itemId=(\d+)", re.IGNORECASE)

def extract_product_id(url: str) -> Optional[str]:
    """Extract product ID from an Instamart product URL."""
    # Try path-based extraction first
    m = _ITEM_ID_RE.search(url)
    if m:
        return m.group(1)
    # Fallback: try query param
    m = _ITEM_PARAM_RE.search(url)
    if m:
        return m.group(1)
    return None


@router.get("/lookup")
async def lookup_product_url(
    url: str = Query(..., description="Instamart product URL"),
    store_id: str = Query(..., description="Instamart store ID to check"),
    min_discount_pct: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    client: httpx.Client = Depends(get_http_client),
    price_history: PriceHistoryService = Depends(get_price_history),
):
    """
    Look up a specific Instamart product URL at a given store.
    Returns availability and deal qualification status.
    """
    product_id = extract_product_id(url)
    if not product_id:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract product ID from URL: {url!r}. "
                   "Expected format: https://www.swiggy.com/instamart/item/<id>"
        )

    product = await asyncio.to_thread(product_at_store, client, store_id, product_id)

    if product is None:
        return {
            "product_id": product_id,
            "url": url,
            "store_id": store_id,
            "found": False,
            "in_stock": False,
            "price": None,
            "mrp": None,
            "discount_pct": None,
            "qualifies": False,
            "image_url": None,
            "brand": None,
        }

    discount_pct = round(((product.mrp - product.price) / product.mrp) * 100, 1) if product.mrp > 0 else 0.0

    qualifies = True
    if min_discount_pct is not None and discount_pct < min_discount_pct:
        qualifies = False
    if max_price is not None and product.price > max_price:
        qualifies = False
    if not product.stock:
        qualifies = False

    return {
        "product_id": product_id,
        "url": url,
        "store_id": store_id,
        "found": True,
        "name": product.name,
        "in_stock": product.stock,
        "price": product.price,
        "mrp": product.mrp,
        "discount_pct": discount_pct,
        "qualifies": qualifies,
        "image_url": product.image_url,
        "brand": product.brand,
    }


@router.post("/parse-url")
async def parse_instamart_url(url: str = Query(...)):
    """Extract and return the product ID from an Instamart URL."""
    product_id = extract_product_id(url)
    if not product_id:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract product ID from URL: {url!r}"
        )
    return {
        "product_id": product_id,
        "canonical_url": f"https://www.swiggy.com/instamart/item/{product_id}"
    }

from sse_starlette.sse import EventSourceResponse
from app.api.schemas import SearchRequest
from app.domain.services.search_orchestrator import DealSearchOrchestrator
import uuid
import json

@router.post("/wishlist/stream")
async def stream_wishlist_search(
    req: SearchRequest,
    client: httpx.Client = Depends(get_http_client),
    store_cache: StoreCache = Depends(get_store_cache),
    price_history: PriceHistoryService = Depends(get_price_history),
):
    """
    Stream deals for a wishlist of exact Instamart product URLs, performing geographic expansion.
    """
    if not req.product_urls:
        raise HTTPException(status_code=400, detail="product_urls cannot be empty for wishlist search")
    
    settings = get_settings()
    lat = req.lat if req.lat is not None else settings.default_lat
    lng = req.lng if req.lng is not None else settings.default_lng
    local_store_id = req.local_store_id if req.local_store_id is not None else settings.local_store_id
    
    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=lat,
        center_lng=lng,
        local_store_id=local_store_id,
        price_history_service=price_history
    )
    
    condition = DealCondition(
        min_discount_pct=req.min_discount_pct,
        max_price=req.max_price,
        price_drop_pct=req.min_price_drop_pct,
        require_historical_low=req.require_historical_low,
        condition_operator=req.condition_operator,
        require_in_stock=req.require_in_stock,
    )
    
    search_id = str(uuid.uuid4())
    
    async def event_generator():
        try:
            async for event_dict in orchestrator.run_url_search(
                search_id=search_id,
                product_urls=req.product_urls,
                condition=condition,
                expansion_radii_km=[1.0, 3.0, 5.0, req.radius_km] if req.radius_km > 5.0 else [1.0, req.radius_km],
                strategy=req.expansion_strategy
            ):
                yield {
                    "event": event_dict["event"],
                    "data": json.dumps(event_dict["data"])
                }
        except asyncio.CancelledError:
            log.info(f"Wishlist search {search_id} cancelled by client.")
        except Exception as e:
            log.error(f"Wishlist search {search_id} failed: {e}", exc_info=True)
            yield {
                "event": "search_error",
                "data": json.dumps({"message": str(e)})
            }
            
    return EventSourceResponse(event_generator())

