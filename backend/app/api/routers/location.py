"""Location resolution and autocomplete endpoints.

This module properly wraps Cart Radar's async SwiggyClient, FlipkartMinutesClient,
and Nominatim geocoder so they run in Worth-It's async FastAPI context without using
asyncio.run() (which breaks inside an already-running event loop).

Root cause of previous failure:
  - `res.external_store_id` → Cart Radar's StoreResolution uses `store_id`, NOT `external_store_id`
  - `asyncio.run()` inside an async FastAPI route → RuntimeError: Event loop already running
  - Sync httpx.Client passed to async SwiggyClient
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.geo.geocoding import nom_forward
from app.platforms.swiggy import SwiggyClient
from app.platforms.flipkart_minutes import FlipkartMinutesClient

log = logging.getLogger("worthit.location")

router = APIRouter()


# ── Response schemas ──────────────────────────────────────────────────────────

class SuggestionItem(BaseModel):
    place_id: str
    display_name: str
    main_text: str
    secondary_text: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class LocationResponse(BaseModel):
    lat: float
    lng: float
    address: str
    title: str
    matched: str
    local_store_id: Optional[str] = None
    fm_store_id: Optional[str] = None


# ── Internal helpers ──────────────────────────────────────────────────────────




async def _resolve_store_id(lat: float, lng: float) -> Optional[str]:
    """Ask Swiggy which store serves this lat/lng.

    Uses SwiggyClient.resolve_store() which returns StoreResolution.
    The correct attribute is `store_id`, NOT `external_store_id`.
    """
    client = SwiggyClient(proxy_url=None, concurrency=2)
    try:
        res = await client.resolve_store(lat, lng)
        # StoreResolution.store_id — correct field name from Cart Radar base.py
        return res.store_id if res and res.store_id else None
    except Exception as e:
        log.warning("Swiggy resolve_store failed for (%.4f, %.4f): %s", lat, lng, e)
        return None
    finally:
        await client.aclose()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/suggest")
async def suggest_locations(q: str = Query(min_length=2)) -> dict:
    """Autocomplete a pincode or locality name.

    Returns Nominatim suggestions with lat/lng pre-resolved so the frontend
    can populate the location immediately on selection without a second request.
    """
    try:
        items = await nom_forward(q, limit=6)
    except Exception as e:
        log.warning("Nominatim suggest failed: %s", e)
        return {"suggestions": []}

    suggestions = []
    for item in items:
        name = item.get("name") or item.get("display_name", "").split(",")[0]
        display = item.get("display_name", "")
        secondary = display.replace(name + ", ", "").strip(", ")
        suggestions.append(
            SuggestionItem(
                place_id=str(item.get("place_id", "")),
                display_name=display,
                main_text=name,
                secondary_text=secondary,
                lat=float(item["lat"]) if "lat" in item else None,
                lng=float(item["lon"]) if "lon" in item else None,
            ).model_dump()
        )

    return {"suggestions": suggestions}


@router.get("/resolve", response_model=LocationResponse)
async def resolve_location_get(
    address: str = Query(..., description="Pincode or address to resolve"),
) -> LocationResponse:
    """Resolve a pincode or address to coordinates + Instamart store ID (GET).

    Flow:
      1. Forward-geocode via Nominatim → lat/lng
      2. Ask Swiggy which store serves that lat/lng (async, no asyncio.run)
      3. Return coords + store_id

    Previously broken because:
      - Used `res.external_store_id` (field does not exist on StoreResolution)
      - Called asyncio.run() inside an already-running async event loop
      - Passed sync httpx.Client to async SwiggyClient
    """
    items = await nom_forward(address, limit=1)
    if not items:
        raise HTTPException(status_code=404, detail=f"Location not found: '{address}'")

    item = items[0]
    lat = float(item["lat"])
    lng = float(item["lon"])
    display_name = item.get("display_name", address)

    import asyncio
    local_store_id = None
    fm_store_id = None
    
    async def resolve_swiggy():
        return await _resolve_store_id(lat, lng)
        
    async def resolve_fm():
        fm_client = FlipkartMinutesClient()
        try:
            res = await fm_client.resolve_store(lat, lng)
            if res and getattr(res, 'serviceable', False) and res.store_id:
                return res.store_id
        except Exception as e:
            log.warning("Flipkart Minutes resolve_store failed for (%.4f, %.4f): %s", lat, lng, e)
        return None

    results = await asyncio.gather(
        resolve_swiggy(),
        resolve_fm(),
        return_exceptions=True
    )
    
    if not isinstance(results[0], Exception):
        local_store_id = results[0]
    if not isinstance(results[1], Exception):
        fm_store_id = results[1]

    return LocationResponse(
        lat=lat,
        lng=lng,
        address=display_name,
        title=address,
        matched="Pincode" if address.strip().isdigit() else "Address",
        local_store_id=local_store_id,
        fm_store_id=fm_store_id,
    )


@router.post("/resolve", response_model=LocationResponse)
async def resolve_location_post(body: dict) -> LocationResponse:
    """POST variant — accepts `{"query": "800014"}`.

    Identical logic to the GET variant.
    """
    query = body.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=422, detail="Missing 'query' field")

    return await resolve_location_get(address=query)
