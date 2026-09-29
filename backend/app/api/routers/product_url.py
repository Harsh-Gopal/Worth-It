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

from app.api.routers.search import get_db, get_price_history, get_store_cache
from app.platforms.swiggy import SwiggyClient

def get_swiggy_client():
    return SwiggyClient()
from app.domain.models.deal import DealCondition
from app.domain.services.price_history_service import PriceHistoryService
from app.geo.store_cache import StoreCache
from app.persistence.database import Database
from app.config import get_settings

# Import from Cart Radar
from app.platforms.swiggy import SwiggyClient
from app.links import extract_product_id, first_url
from app.domain.services.price_history_service import PriceHistoryService
from app.persistence.database import Database
from app.config import get_settings

log = logging.getLogger("product_url_router")
router = APIRouter()


@router.get("/lookup")
async def lookup_product_url(
    url: str = Query(..., description="Instamart product URL"),
    store_id: str = Query(..., description="Instamart store ID to check"),
    lat: Optional[float] = Query(None, description="User latitude"),
    lng: Optional[float] = Query(None, description="User longitude"),
    max_price: Optional[float] = Query(None),
    client: SwiggyClient = Depends(get_swiggy_client),
    price_history: PriceHistoryService = Depends(get_price_history),
):
    """
    Look up a specific Instamart product URL at a given store.
    Returns availability and deal qualification status.
    """
    log.info(f"[WISHLIST] Received lookup input: {url}")
    from app.links import extract_canonical_url, extract_product_id
    platform, canonical_url, error_code = extract_canonical_url(url)
    
    if error_code == "URL_EXTRACTION_FAILED":
        log.warning(f"[WISHLIST] URL extraction failed for: {url}")
        raise HTTPException(status_code=400, detail="No supported product link was found in the pasted text.")
    if error_code == "UNSUPPORTED_PLATFORM":
        log.warning(f"[WISHLIST] Unsupported platform for: {url}")
        raise HTTPException(status_code=400, detail="Unsupported shopping platform. Please paste a valid product URL.")
    if error_code == "AMBIGUOUS_URLS":
        log.warning(f"[WISHLIST] Ambiguous URLs found in: {url}")
        raise HTTPException(status_code=400, detail="Multiple product URLs found. Please submit only one product link at a time.")
    if not platform or not canonical_url:
        log.warning(f"[WISHLIST] Invalid URL format for: {url}")
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract product ID from URL: {url!r}. "
                   "Expected format: https://www.swiggy.com/instamart/item/<id>"
        )
        
    log.info(f"[WISHLIST] URL extracted and Platform detected: {platform}, {canonical_url}")
    _, product_id = extract_product_id(canonical_url)

    from app.platforms.factory import get_platform_client
    try:
        plat_client = get_platform_client(platform)
        log.info(f"[WISHLIST] Adapter selected: {platform}")
    except Exception as e:
        log.warning(f"[WISHLIST] Adapter selection failed for platform {platform}: {e}")
        raise HTTPException(status_code=400, detail=f"Unsupported platform. Supported platforms: Instamart, Blinkit, Zepto and Flipkart Minutes.")
        
    store_cache_inst = get_store_cache()
    # Frontend passes the selected Instamart store. We use its coordinates if explicit lat/lng are not provided.
    store = store_cache_inst.get_store(store_id, "instamart")
    
    effective_lat = lat if lat is not None else (store.lat if store else 12.9716)
    effective_lng = lng if lng is not None else (store.lng if store else 77.5946)
        
    platform_display = {
        "swiggy": "Instamart", "instamart": "Instamart",
        "blinkit": "Blinkit", "zepto": "Zepto", "minutes": "Flipkart Minutes",
        "bigbasket": "BigBasket", "bbnow": "BBNow",
    }.get(platform, platform.capitalize())

    import asyncio
    try:
        if platform in ("swiggy", "instamart"):
            product = await asyncio.wait_for(plat_client.product_at_store(product_id, store_id, effective_lat, effective_lng), timeout=25.0)
        else:
            # We must use product_at_location because the store_id provided is for Instamart
            product = await asyncio.wait_for(plat_client.product_at_location(product_id, effective_lat, effective_lng), timeout=25.0)
    except Exception as e:
        log.error(f"Error fetching product from {platform_display}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"{platform_display} is temporarily unavailable. Please try again."
        )

    if not product or product.status == 'error':
        raise HTTPException(
            status_code=500,
            detail=f"{platform_display} is temporarily unavailable. Please try again."
        )
        
    # We removed the not_carried 404 block so users can track products even if currently unserviceable at their store.

    # Ensure platform is set on the product if we got one, useful later
    if product:
        product.platform = platform

    fallback_name = f"Product {product_id}"
    try:
        import urllib.parse
        path_parts = urllib.parse.urlparse(url).path.strip('/').split('/')
        for i, part in enumerate(path_parts):
            if part in ('pn', 'prn', 'pr', 'p') and i + 1 < len(path_parts):
                fallback_name = path_parts[i+1].replace('-', ' ').title()
                break
    except Exception:
        pass

    if product.status != 'in_stock':
        return {
            "product_id": product_id,
            "url": url,
            "store_id": store_id,
            "found": True,
            "name": product.name or fallback_name,
            "in_stock": False,
            "price": product.price,
            "mrp": product.mrp,
            "discount_pct": None,
            "qualifies": False,
            "image_url": product.image_url,
            "brand": product.brand,
            "stock": False,
            "qualifies_as_deal": False,
            "is_historical_low": False,
            "discount_percent": 0.0,
            "price_drop_percent": None,
            "historical_low": None,
            "trigger_reasons": [],
        }

    discount_pct = round(((product.mrp - product.price) / product.mrp) * 100, 1) if product.mrp > 0 else 0.0

    qualifies = True
    if max_price is not None and product.price > max_price:
        qualifies = False
    if product.status != 'in_stock':
        qualifies = False

    return {
        "product_id": product_id,
        "url": url,
        "store_id": store_id,
        "found": True,
        "name": product.name,
        "price": product.price,
        "mrp": product.mrp,
        "brand": product.brand,
        "image_url": product.image_url,
        "stock": product.status == 'in_stock',
        "qualifies_as_deal": False,
        "is_historical_low": False,
        "discount_percent": 0.0,
        "price_drop_percent": None,
        "historical_low": None,
        "trigger_reasons": [],
    }


@router.post("/parse-url")
async def parse_product_url(url: str = Query(...)):
    """Extract and return the product ID from a product URL."""
    from app.links import extract_canonical_url
    platform, canonical_url, error_code = extract_canonical_url(url)
    
    if error_code == "URL_EXTRACTION_FAILED":
        raise HTTPException(status_code=400, detail="No supported product link was found in the pasted text.")
    if error_code == "UNSUPPORTED_PLATFORM":
        raise HTTPException(status_code=400, detail="Unsupported shopping platform. Please paste a valid product URL.")
    if error_code == "AMBIGUOUS_URLS":
        raise HTTPException(status_code=400, detail="Multiple product URLs found. Please submit only one product link at a time.")
    if not platform or not canonical_url:
        raise HTTPException(status_code=400, detail="Could not extract product ID from URL.")
        
    # We still need to return product_id for frontend compatibility, though canonical_url is what really matters.
    # extract_canonical_url already verified it works, so we can just extract the product_id again or parse it.
    from app.links import extract_product_id
    _, product_id = extract_product_id(canonical_url)

    return {
        "product_id": product_id,
        "canonical_url": canonical_url
    }

from sse_starlette.sse import EventSourceResponse
from app.api.schemas import SearchRequest
from app.domain.services.search_orchestrator import DealSearchOrchestrator
import uuid
import json

@router.post("/wishlist/stream")
async def stream_wishlist_search(
    req: SearchRequest,
    client: SwiggyClient = Depends(get_swiggy_client),
    store_cache: StoreCache = Depends(get_store_cache),
    price_history: PriceHistoryService = Depends(get_price_history),
):
    """
    Stream deals for a wishlist of exact Instamart product URLs, performing geographic expansion.
    """
    if not req.product_urls:
        raise HTTPException(status_code=400, detail="product_urls cannot be empty for wishlist search")
    
    settings = get_settings()
    lat = req.lat if req.lat is not None else settings.center_lat
    lng = req.lng if req.lng is not None else settings.center_lng
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

