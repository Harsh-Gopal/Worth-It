import asyncio
import httpx
from app.platforms.swiggy import _waf_session, _make_location_cookie

async def main():
    await _waf_session.ensure(12.9716, 77.6411)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": _make_location_cookie(12.9716, 77.6411)
    }
    if _waf_session.device_id:
        headers["x-device-id"] = _waf_session.device_id
        
    async with httpx.AsyncClient() as c:
        for url in [
            "https://www.swiggy.com/api/instamart/item/8ILS98WFQR",
            "https://www.swiggy.com/api/instamart/item/v1/8ILS98WFQR",
            "https://www.swiggy.com/api/instamart/item/v2/8ILS98WFQR",
            f"https://www.swiggy.com/api/instamart/item/8ILS98WFQR?storeId=1395721"
        ]:
            r = await c.get(url, headers=headers, cookies=_waf_session.cookies)
            print(f"URL: {url} -> {r.status_code}")

asyncio.run(main())
