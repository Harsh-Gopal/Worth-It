import logging
from typing import Optional
import httpx

log = logging.getLogger("worthit.geocoding")

_NOM_HEADERS = {"User-Agent": "WorthIt/1.0 (local-dev)"}
_NOM_BASE = "https://nominatim.openstreetmap.org"

_GEO_CACHE = {}

async def nom_forward(query: str, limit: int = 5) -> list[dict]:
    """Forward geocode via Nominatim. Returns raw Nominatim items."""
    async with httpx.AsyncClient(timeout=10.0, headers=_NOM_HEADERS) as c:
        resp = await c.get(
            f"{_NOM_BASE}/search",
            params={"q": query, "format": "json", "countrycodes": "in", "limit": limit},
        )
        if resp.status_code != 200:
            return []
        return resp.json()

async def nom_reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """Reverse geocode via Nominatim to get pincode. Uses caching."""
    rlat, rlng = round(lat, 4), round(lng, 4)
    if (rlat, rlng) in _GEO_CACHE:
        return _GEO_CACHE[(rlat, rlng)]
        
    try:
        async with httpx.AsyncClient(timeout=8.0, headers=_NOM_HEADERS) as c:
            resp = await c.get(
                f"{_NOM_BASE}/reverse",
                params={"lat": rlat, "lon": rlng, "format": "json", "addressdetails": 1},
            )
            if resp.status_code == 200:
                data = resp.json()
                pincode = data.get("address", {}).get("postcode")
                _GEO_CACHE[(rlat, rlng)] = pincode
                return pincode
    except Exception as e:
        log.warning("Nominatim reverse-geocode failed: %s", e)
    return None
