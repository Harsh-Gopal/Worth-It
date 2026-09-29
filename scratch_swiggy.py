import asyncio
from app.platforms.swiggy import SwiggyClient
from app.core.browser import BrowserManager
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    client = SwiggyClient()
    # Test lat lng (Indiranagar, Bangalore roughly)
    lat, lng = 12.9716, 77.6411
    
    # 1. Resolve store
    store_res = await client.resolve_store(lat, lng)
    print("Store Resolution:", store_res)
    
    store_id = store_res.store_id
    if not store_id:
        print("No store id!")
        return

    # 2. Search
    results = await client.search("milk", store_id, lat, lng)
    print(f"Found {len(results)} results")
    for i, r in enumerate(results[:3]):
        print(f"{i}: {r}")

    await BrowserManager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
