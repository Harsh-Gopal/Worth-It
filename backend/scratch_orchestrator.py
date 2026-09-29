import asyncio
from app.platforms.swiggy import SwiggyClient
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.geo.store_cache import StoreCache
from app.core.browser import BrowserManager
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    client = SwiggyClient()
    # Test lat lng (Indiranagar, Bangalore roughly)
    lat, lng = 12.9716, 77.6411
    
    # Resolve store
    store_res = await client.resolve_store(lat, lng)
    print("Store Resolution:", store_res)
    
    store_id = store_res.store_id
    
    store_cache = StoreCache("test_stores.json")
    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=lat,
        center_lng=lng,
        local_store_id=store_id
    )

    events = orchestrator.run_search(
        search_id="test_123",
        keyword="milk",
        match_keywords=["milk"],
        expansion_radii_km=[2.0],
        strategy="NEARBY_FIRST"
    )

    async for event in events:
        print(f"EVENT: {event.event}")
        if event.event == 'deal_found':
            print(f"DEAL: {event.data['product']['name']}")

    await BrowserManager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
