import asyncio
from app.platforms.zepto.client import ZeptoPlaywrightSession, BFF_BASE
import json
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing Zepto Search via HTTP...")
    async with ZeptoPlaywrightSession() as session:
        # Resolve store first to get context
        # 12.9298, 77.6293 is Koramangala
        res = await session.probe_location(12.9298, 77.6293)
        store_id = res.get("store_id")
        print(f"Store ID: {store_id}")
        
        # Test Search
        url = f"{BFF_BASE}/search-service/search?query=whey&pageNumber=0&storeId={store_id}"
        api_resp = await session.context.request.get(
            url,
            headers={
                "platform": "WEB",
                "tenant": "ZEPTO",
                "app_version": "16.2.11",
                "storeId": store_id
            }
        )
        print(f"Status: {api_resp.status}")
        data = await api_resp.json()
        print(json.dumps(data, indent=2)[:1000])

if __name__ == "__main__":
    asyncio.run(main())
