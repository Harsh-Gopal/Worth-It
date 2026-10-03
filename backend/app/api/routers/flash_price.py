"""
Flash Price Router
==================

Standalone API endpoints for the Instamart Flash / Promotional Price Tracker.

GET /api/flash-price/lookup
  Fetch the flash (promotional) price for a single Instamart product URL.

GET /api/flash-price/batch
  Fetch flash prices for up to 5 Instamart product URLs at once.

These endpoints are completely independent of the existing /api/product/lookup
and /api/search routes. Normal product tracking cannot regress.
"""

import asyncio
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from app.platforms.promo_price import fetch_flash_price, FlashPriceResult
from app.links import extract_product_id, detect_platform

log = logging.getLogger("flash_price_router")

router = APIRouter()


def _extract_instamart_id(url: str) -> str | None:
    """Extract an Instamart product ID from a URL. Returns None if not an Instamart URL."""
    platform, product_id = extract_product_id(url)
    if platform == "swiggy" and product_id:
        return product_id
    return None


def _result_to_dict(r: FlashPriceResult) -> dict:
    return {
        "product_id": r.product_id,
        "name": r.name,
        "brand": r.brand,
        "image_url": r.image_url,
        "normal_price": r.normal_price,
        "mrp": r.mrp,
        "special_price": r.special_price,
        "non_flash_price": r.non_flash_price,
        "flash_end_time": r.flash_end_time,
        "redemption_limit": r.redemption_limit,
        "extraction_method": r.extraction_method,
        "serviceable": r.serviceable,
        "has_flash_sale": r.special_price is not None,
        "error": r.error,
    }


@router.get("/lookup")
async def flash_price_lookup(
    url: str = Query(..., description="Instamart product URL"),
    lat: float = Query(..., description="User latitude for serviceability check"),
    lng: float = Query(..., description="User longitude for serviceability check"),
):
    """
    Look up the flash/promotional price for a single Instamart product URL.

    Returns both the normal price and the special (flash-sale) price if active.
    `special_price` is null when no flash sale is running for this product.
    """
    product_id = _extract_instamart_id(url)
    if not product_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract an Instamart product ID from the provided URL. "
                   "Please use an Instamart product URL (swiggy.com/instamart/... or instamart.in/item/...).",
        )

    log.info("flash_price: lookup product_id=%s lat=%.4f lng=%.4f", product_id, lat, lng)

    try:
        result = await asyncio.wait_for(
            fetch_flash_price(product_id, lat, lng),
            timeout=25.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Flash price lookup timed out (25 s). Try again.")
    except Exception as e:
        log.error("flash_price: unexpected error for %s: %s", product_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Flash price extraction failed: {e}")

    return _result_to_dict(result)


@router.get("/batch")
async def flash_price_batch(
    urls: str = Query(..., description="Comma-separated Instamart product URLs (max 5)"),
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
):
    """
    Fetch flash prices for up to 5 Instamart products concurrently.

    Returns a list of results in the same order as the input URLs.
    Each item has the same shape as the /lookup response.
    """
    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    if not url_list:
        raise HTTPException(status_code=400, detail="No URLs provided.")
    if len(url_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 URLs per batch request.")

    id_url_pairs: list[tuple[str, str | None]] = []
    for url in url_list:
        pid = _extract_instamart_id(url)
        id_url_pairs.append((url, pid))

    invalid = [url for url, pid in id_url_pairs if pid is None]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Non-Instamart URL(s) detected: {invalid}. Only Instamart URLs are supported.",
        )

    log.info("flash_price: batch %d products lat=%.4f lng=%.4f", len(id_url_pairs), lat, lng)

    async def _safe_fetch(product_id: str) -> FlashPriceResult:
        try:
            return await asyncio.wait_for(
                fetch_flash_price(product_id, lat, lng),
                timeout=25.0,
            )
        except asyncio.TimeoutError:
            from app.platforms.promo_price import FlashPriceResult
            return FlashPriceResult(product_id=product_id, error="timeout")
        except Exception as e:
            from app.platforms.promo_price import FlashPriceResult
            return FlashPriceResult(product_id=product_id, error=str(e))

    tasks = [_safe_fetch(pid) for _, pid in id_url_pairs]  # type: ignore[misc]
    results = await asyncio.gather(*tasks)

    return [_result_to_dict(r) for r in results]
