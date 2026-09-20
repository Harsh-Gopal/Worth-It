import asyncio
import logging
from app.config import get_settings
from app.platforms.swiggy import SwiggyClient
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.domain.models.deal import DealCondition
from app.geo.store_cache import StoreCache

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("swiggy").setLevel(logging.DEBUG)
logging.getLogger("orchestrator").setLevel(logging.DEBUG)

async def test_protein_discovery():
    settings = get_settings()
    store_cache = StoreCache(settings.store_cache_path)
    client = SwiggyClient()
    
    # 801505 coordinates (approximate, we need to resolve it first, but let's use the geocoder or just pass 801505)
    # Actually, Worth-It resolves pincode 801505 to lat/lng first using location API.
    # I'll call the location API's geocoding method to get lat/lng for 801505.
    
    import httpx
    # 801505 = IIT Patna, Bihta
    async with httpx.AsyncClient(headers={"User-Agent": "WorthIt/1.0 (local-dev)"}) as c:
        resp = await c.get("https://nominatim.openstreetmap.org/search?q=801505+India&format=json&limit=1")
        data = resp.json()
        if not data:
            print("Geocoding failed")
            return
        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
    print(f"801505 resolved to lat={lat}, lng={lng}")

    # Resolve store
    store_res = await client.resolve_store(lat, lng)
    print(f"Store resolved: {store_res}")

    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=lat,
        center_lng=lng,
        local_store_id=store_res.store_id if store_res else "synthetic_0_0"
    )

    condition = DealCondition(min_discount_pct=80.0)

    print(f"Starting combined search...")
    events = []
    async for event in orchestrator.run_combined_search(
        search_id="test_protein",
        keyword="Protein",
        product_urls=[],
        match_keywords=["Protein"],
        exclude_keywords=None,
        condition=condition,
        expansion_radii_km=[2.0, 5.0],
        strategy="spiral"
    ):
        events.append(event)
        if event["event"] == "deal_found":
            deal = event["data"]
            print(f"*** DEAL FOUND ***: {deal}")
        else:
            print(f"Event: {event['event']}")

    print(f"Total events emitted: {len(events)}")

if __name__ == "__main__":
    asyncio.run(test_protein_discovery())
