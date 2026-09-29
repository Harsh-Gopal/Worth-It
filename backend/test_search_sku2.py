import asyncio
from app.platforms.swiggy import SwiggyClient

async def main():
    client = SwiggyClient()
    products = await client.search("8ILS98WFQR", "1395721", 12.9716, 77.6411)
    found = False
    for p in products:
        if p.external_product_id == "8ILS98WFQR":
            print("Found!", p)
            found = True
            break
    if not found:
        print("Not found in results")

asyncio.run(main())
