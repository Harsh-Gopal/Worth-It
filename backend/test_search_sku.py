import asyncio
import json
from app.platforms.swiggy import SwiggyClient

async def main():
    client = SwiggyClient()
    products = await client.search("8ILS98WFQR", "1395721", 12.9716, 77.6411)
    print(f"Found {len(products)} products for SKU search")
    if products:
        print(products[0])

asyncio.run(main())
