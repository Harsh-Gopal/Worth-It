import asyncio
import logging
import json
from app.platforms.swiggy import SwiggyClient

logging.basicConfig(level=logging.DEBUG)

async def main():
    client = SwiggyClient(None, 5)
    lat = 25.6075768
    lng = 85.083029
    store = await client.resolve_store(lat, lng)
    
    await client.ensure_waf_session(lat, lng)
    import urllib.parse
    sid = store.store_id
    url = f"https://www.swiggy.com/api/instamart/search/v2?offset=0&ageConsent=false&storeId={sid}&primaryStoreId={sid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
        "content-type": "application/json",
        "x-device-id": urllib.parse.unquote(client._waf_cookies.get("deviceId", "")).removeprefix("s:").split(".")[0],
    }
    body = {
        "facets": [], "sortAttribute": "", "query": "Coconut", "search_results_offset": "0", "page_type": "INSTAMART_SEARCH_PAGE"
    }
    import httpx
    async with httpx.AsyncClient(timeout=20, cookies=client._waf_cookies) as c:
        resp = await c.post(url, headers=headers, json=body)
        data = resp.json()
        
        with open("coconut_search_raw.json", "w") as f:
            json.dump(data, f, indent=2)
            
        count = 0
        for card in ((data.get("data") or {}).get("cards") or []):
            grid = (((card.get("card") or {}).get("card") or {}).get("gridElements") or {}).get("infoWithStyle") or {}
            for item in grid.get("items") or []:
                print(item.get("displayName") or "Unknown item", item.keys())
                count += 1
        print(f"Total items found: {count}")

if __name__ == "__main__":
    asyncio.run(main())
