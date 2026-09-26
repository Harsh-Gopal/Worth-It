import asyncio
import logging
from app.platforms.zepto.client import ZeptoClient, _close_firefox_browser

logging.basicConfig(level=logging.INFO)

async def main():
    client = ZeptoClient()
    lat, lng = 12.9716, 77.5946
    
    res = await client.resolve_store(lat, lng)
    
    print("Testing search for 'Sports & Fitness' (is_category=False)...")
    results = await client.search("Sports & Fitness", res.store_id, lat, lng, is_category=False)
    print(f"Found {len(results)} products!")
    for r in results[:10]:
        print(f" - {r.name} (Brand: {r.brand})")
        
    await _close_firefox_browser()

if __name__ == "__main__":
    asyncio.run(main())
