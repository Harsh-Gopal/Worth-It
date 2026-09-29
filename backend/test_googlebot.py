import asyncio
import httpx
async def main():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    async with httpx.AsyncClient() as c:
        r = await c.get("https://www.swiggy.com/stores/instamart/item/F9UK3KLPCI", headers=headers)
        print("Status:", r.status_code)
        if r.status_code == 200:
            print("Length:", len(r.text))
            print("Contains productV2:", "productV2" in r.text)

asyncio.run(main())
