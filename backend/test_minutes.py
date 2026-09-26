import asyncio
import logging
import sys

from app.platforms.flipkart import FlipkartMinutesClient

logging.basicConfig(level=logging.INFO)

async def main():
    client = FlipkartMinutesClient()
    # Use a product id and a known location (e.g., Patna)
    # 25.6012, 85.0697
    print("Resolving store for Flipkart Minutes...")
    res = await client.resolve_store(lat=25.6012, lng=85.0697, product_id="itme3a8cf822f3c0")
    print("Store resolution:", res)
    
    if res.serviceable:
        prod = await client.product_at_store("itme3a8cf822f3c0", res.store_id, lat=25.6012, lng=85.0697)
        print("Product result:", prod)
    else:
        print("Not serviceable")

    await client.aclose()
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
