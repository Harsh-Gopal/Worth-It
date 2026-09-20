import asyncio
from app.platforms.swiggy import SwiggyClient

async def main():
    client = SwiggyClient(None, 5)
    lat = 25.6075768
    lng = 85.083029
    store = await client.resolve_store(lat, lng)
    results = await client.search("Coconut", store.store_id, lat, lng)
    for r in results:
        print(f"{r.name}: {r.price} (MRP {r.mrp})")

if __name__ == "__main__":
    asyncio.run(main())
