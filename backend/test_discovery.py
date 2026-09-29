import asyncio
import httpx
from app.domain.services.product_discovery import ProductDiscoveryEngine

async def main():
    async with httpx.AsyncClient() as c:
        engine = ProductDiscoveryEngine(c, "1395721", 12.9716, 77.6411)
        res = await engine.discover("milk", match_keywords=["milk"])
        print(f"Discovered {len(res)} products")
        if res:
            print(res[0])

asyncio.run(main())
