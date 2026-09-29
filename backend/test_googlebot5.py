import asyncio
import httpx
from app.platforms.swiggy import _waf_session, _make_location_cookie

async def main():
    await _waf_session.ensure(12.9716, 77.6411)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": _make_location_cookie(12.9716, 77.6411)
    }
    async with httpx.AsyncClient() as c:
        r = await c.get("https://www.swiggy.com/instamart/item/8ILS98WFQR", headers=headers, cookies=_waf_session.cookies)
        print("Status:", r.status_code)
        print("Contains productV2:", "productV2" in r.text)
        print("productV2 is null:", '"productV2":{"inError":false,"itemData":null' in r.text)

asyncio.run(main())
