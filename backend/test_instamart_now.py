import asyncio
import logging
from app.platforms.swiggy import SwiggyClient
from app.core.browser import BrowserManager

logging.basicConfig(level=logging.INFO)

async def main():
    client = SwiggyClient()
    print(f"Platform: {client.platform_name}")
    
    # Try searching
    lat, lng = 28.5355, 77.3910 # random location
    print("Resolving store...")
    store = await client.resolve_store(lat, lng)
    print(f"Store: {store}")
    
    if store and store.serviceable:
        print("Searching for milk...")
        results = await client.search(query="milk", store_id=store.store_id, lat=lat, lng=lng)
        for r in results:
            print(f"- {r.name}: price={r.price}, mrp={r.mrp}")

    await BrowserManager.close()

if __name__ == "__main__":
    asyncio.run(main())
