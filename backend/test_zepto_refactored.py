import asyncio
import logging
import sys

from app.platforms.zepto.client import ZeptoClient

logging.basicConfig(level=logging.INFO)

async def main():
    client = ZeptoClient()
    # E.g. search for "milk" at 28.5355, 77.2410 (Delhi)
    lat = 28.5355
    lng = 77.2410
    print("Probing location...")
    store = await client.resolve_store(lat, lng)
    print("Store:", store)
    if store.serviceable:
        print("Searching for milk...")
        results = await client.search("milk", store.store_id, lat, lng)
        for r in results[:5]:
            print("Found:", r.name, r.price, r.status)
            
        if results:
            print("Checking product_at_store for first result...")
            prod_id = results[0].external_product_id
            prod = await client.product_at_store(prod_id, store.store_id, lat, lng)
            print("Product result:", prod.status, prod.price)
    
    await client.aclose()
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
