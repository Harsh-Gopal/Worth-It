import asyncio
import logging
from app.platforms.swiggy import SwiggyClient

logging.basicConfig(level=logging.INFO)

async def main():
    client = SwiggyClient(None, 5)
    lat = 25.6075768
    lng = 85.083029
    store = await client.resolve_store(lat, lng)
    results = await client.search("Chakkizza Multi-Grain Atta", store.store_id, lat, lng)
    for res in results:
        print(f"RES: {res.name}, price={res.price}, mrp={res.mrp}")

if __name__ == "__main__":
    asyncio.run(main())
