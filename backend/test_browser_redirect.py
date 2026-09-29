import asyncio
import httpx
async def main():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with httpx.AsyncClient() as c:
        r = await c.get("https://www.swiggy.com/instamart/item/8ILS98WFQR", headers=headers, follow_redirects=False)
        print("Status:", r.status_code)
        print("Location:", r.headers.get("Location"))
asyncio.run(main())
