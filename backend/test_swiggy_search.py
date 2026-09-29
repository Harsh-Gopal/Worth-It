import asyncio
from app.platforms.swiggy import SwiggyClient

async def main():
    client = SwiggyClient()
    results = await client.search("lays", "1395721", 12.9716, 77.6411)
    if results:
        print("First result ext_id:", results[0].external_product_id)
        
        # Test product_at_store
        res2 = await client.product_at_store(results[0].external_product_id, "1395721", 12.9716, 77.6411)
        print("product_at_store result:", res2)

asyncio.run(main())
