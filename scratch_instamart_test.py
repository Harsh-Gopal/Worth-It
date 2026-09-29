import asyncio
import json
from app.platforms.swiggy import SwiggyClient

import logging
logging.basicConfig(level=logging.DEBUG)

async def main():
    client = SwiggyClient()
    # Provide a typical lat/lng for Bangalore (e.g. Indiranagar)
    res = await client.resolve_store(12.9716, 77.6411)
    print("Resolved Store ID:", res.store_id if res else None)
    
    if res and res.store_id:
        print(f"\nSearching 'milk' at store {res.store_id}...")
        products = await client.search("milk", res.store_id, 12.9716, 77.6411)
        print(f"Found {len(products)} products.")
        if products:
            print(products[0])
            print("First item dict:", json.dumps(products[0].__dict__, default=str))
            
            print(f"\nTesting product_at_store for {products[0].external_product_id}...")
            prod = await client.product_at_store(products[0].external_product_id, res.store_id, 12.9716, 77.6411)
            print("product_at_store:", prod)
            
            import httpx
            async with httpx.AsyncClient() as c:
                r = await c.get(f"https://www.swiggy.com/stores/instamart/item/{products[0].external_product_id}", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                with open("swiggy_test.html", "w") as f:
                    f.write(r.text)

if __name__ == "__main__":
    asyncio.run(main())
