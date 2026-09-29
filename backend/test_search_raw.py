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
        "facets": [], "sortAttribute": "", "query": "milk",
        "search_results_offset": "0", "page_type": "INSTAMART_SEARCH_PAGE",
    }
    async with httpx.AsyncClient() as c:
        resp = await c.post(
            f"https://www.swiggy.com/api/instamart/search/v2?storeId={res.store_id}",
            headers=headers, json=body, cookies=_waf_session.cookies
        )
        print(json.dumps(resp.json()["data"]["cards"][0], indent=2)[:1500])

asyncio.run(main())
