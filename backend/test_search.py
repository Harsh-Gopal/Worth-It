import asyncio
import logging
from app.platforms.swiggy import SwiggyClient

logging.basicConfig(level=logging.DEBUG)

async def main():
    client = SwiggyClient(None, 5)
    # Pincode 800014
    lat = 25.6075768
    lng = 85.083029
    
    # 1. Resolve store
    store = await client.resolve_store(lat, lng)
    print(f"Store: {store}")
    
    # 2. Search Coconut
    results = await client.search("Coconut", store.store_id, lat, lng)
    print(f"Results for Coconut: {len(results)}")
    for r in results:
        print(f" - {r.name}: {r.price} (MRP {r.mrp})")
        
    # 3. Search Chakkizza
    results2 = await client.search("Chakkizza Multi-Grain Atta", store.store_id, lat, lng)
    print(f"Results for Chakkizza: {len(results2)}")
    for r in results2:
        print(f" - {r.name}: {r.price} (MRP {r.mrp})")

if __name__ == "__main__":
    asyncio.run(main())
