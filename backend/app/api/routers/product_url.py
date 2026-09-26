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
from app.links import extract_product_id
from app.domain.services.price_history_service import PriceHistoryService
from app.persistence.database import Database
from app.config import get_settings

log = logging.getLogger("product_url_router")
router = APIRouter()


@router.get("/lookup")
async def lookup_product_url(
    url: str = Query(..., description="Instamart product URL"),
    store_id: str = Query(..., description="Instamart store ID to check"),
    max_price: Optional[float] = Query(None),
    client: SwiggyClient = Depends(get_swiggy_client),
    price_history: PriceHistoryService = Depends(get_price_history),
):
    """
    Look up a specific Instamart product URL at a given store.
    Returns availability and deal qualification status.
    """
    import re
    urls = re.findall(r"https?://\S+", url)
    if len(urls) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple URLs found. Please submit only one product link at a time."
        )
        
    extracted = extract_product_id(url)
    if not extracted or not extracted[0] or not extracted[1]:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract product ID from URL: {url!r}. "
                   "Expected format: https://www.swiggy.com/instamart/item/<id>"
        )
    platform = extracted[0]
    product_id = extracted[1]

    from app.platforms.factory import get_platform_client
    try:
        plat_client = get_platform_client(platform)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unsupported platform. Supported platforms: Instamart, Blinkit, Zepto and Flipkart Minutes.")
        
    store_cache_inst = get_store_cache()
    # Frontend passes the selected Instamart store. We use its coordinates.
    store = store_cache_inst.get_store(store_id, "instamart")
    lat = store.lat if store else 12.9716
    lng = store.lng if store else 77.5946
        
    platform_display = {
        "swiggy": "Instamart", "instamart": "Instamart",
        "blinkit": "Blinkit", "zepto": "Zepto", "minutes": "Flipkart Minutes"
    }.get(platform, platform.capitalize())

    try:
        product = await plat_client.product_at_store(product_id, store_id, lat, lng)
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
        
    if product.status == 'not_carried':
        raise HTTPException(
            status_code=404,
            detail=f"Could not resolve this {platform_display} product."
        )

    # Ensure platform is set on the product if we got one, useful later
    if product:
        product.platform = platform

    if product.status != 'in_stock':
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
            "image_url": product.image_url,
            "brand": product.brand,
            "error": f"Could not resolve this {platform_display} product."
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
    import re
    urls = re.findall(r"https?://\S+", url)
    if len(urls) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple URLs found. Please submit only one product link at a time."
        )
        
    extracted = extract_product_id(url)
    if not extracted or not extracted[0] or not extracted[1]:
        raise HTTPException(
            status_code=400,
            detail=f"Please enter a valid Instamart, Blinkit, Zepto or Flipkart Minutes product URL."
        )
    platform = extracted[0]
    product_id = extracted[1]
    
    canonical_url = url # fallback
    if platform == "swiggy":
        canonical_url = f"https://www.swiggy.com/instamart/item/{product_id}"
    elif platform == "zepto":
        canonical_url = f"https://www.zeptonow.com/pn/product/pvid/{product_id}"
    elif platform == "blinkit":
        canonical_url = f"https://blinkit.com/prn/product/prid/{product_id}"
    elif platform == "flipkart" or platform == "minutes":
        canonical_url = f"https://www.flipkart.com/product/p/itme?pid={product_id}"
        
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

