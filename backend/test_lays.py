import asyncio
from app.platforms.swiggy import SwiggyClient
async def main():
    client = SwiggyClient()
    products = await client.search("lays", "1395721", 12.9716, 77.6411)
    for p in products:
        if p.price < p.mrp:
            print(f"Deal! {p.name}: {p.price} vs {p.mrp}")
        else:
            print(f"No deal: {p.name}: {p.price} vs {p.mrp}")

asyncio.run(main())
