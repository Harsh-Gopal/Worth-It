import asyncio
import httpx
async def main():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    async with httpx.AsyncClient() as c:
        r = await c.get("https://www.swiggy.com/stores/instamart/item/8ILS98WFQR", headers=headers)
        print("Status:", r.status_code)
        if r.status_code == 200:
            print("Length:", len(r.text))
            print("Contains productV2:", "productV2" in r.text)
            print("productV2 is null:", '"productV2":{"inError":false,"itemData":null' in r.text)

asyncio.run(main())
