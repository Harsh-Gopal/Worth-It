import asyncio
import httpx
from app.platforms.swiggy import _make_location_cookie

async def main():
    url = "https://www.swiggy.com/instamart"
    headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Accept-Encoding": "gzip, deflate",
        "Cookie": _make_location_cookie(25.6075, 85.0830)
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, headers=headers)
        html = resp.text
        
        import re
        sid_m = re.search(r'"storeDetailsV2"\s*:\s*\{"storeId"\s*:\s*"(\d+)"', html)
        print("REGEX storeDetailsV2:", sid_m)
        sid2_m = re.findall(r'"storeId"\s*:\s*"(\d+)"', html)
        print("ALL storeIds:", sid2_m)

if __name__ == "__main__":
    asyncio.run(main())
