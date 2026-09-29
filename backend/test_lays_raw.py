import asyncio
import json
from app.platforms.swiggy import SwiggyClient, _waf_session
import httpx

async def main():
    client = SwiggyClient()
    res = await client.resolve_store(12.9716, 77.6411)
    
    await _waf_session.ensure(12.9716, 77.6411)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "content-type": "application/json",
    }
    if _waf_session.device_id:
        headers["x-device-id"] = _waf_session.device_id
    body = {
        "facets": [], "sortAttribute": "", "query": "lays",
        "search_results_offset": "0", "page_type": "INSTAMART_SEARCH_PAGE",
    }
    async with httpx.AsyncClient() as c:
        resp = await c.post(
            f"https://www.swiggy.com/api/instamart/search/v2?storeId={res.store_id}",
            headers=headers, json=body, cookies=_waf_session.cookies
        )
        data = resp.json()
        for card in data["data"]["cards"]:
            inner = card.get("card", {}).get("card", {})
            if "gridElements" in inner:
                items = inner["gridElements"].get("infoWithStyle", {}).get("items", [])
                if items:
                    for i in items:
                        if i.get("price", {}).get("mrp", {}).get("units", "0") != i.get("price", {}).get("offerPrice", {}).get("units", "0"):
                            print(json.dumps(i, indent=2))
                            return

asyncio.run(main())
