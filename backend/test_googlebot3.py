import asyncio
import httpx
import json
import urllib.parse
async def main():
    val = json.dumps({"lat": 12.9716, "lng": 77.6411, "address": "India"})
    cookie = "userLocation=" + urllib.parse.quote(val)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Cookie": cookie
    }
    async with httpx.AsyncClient() as c:
        r = await c.get("https://www.swiggy.com/stores/instamart/item/8ILS98WFQR", headers=headers)
        print("Contains productV2:", "productV2" in r.text)
        print("productV2 is null:", '"productV2":{"inError":false,"itemData":null' in r.text)

asyncio.run(main())
