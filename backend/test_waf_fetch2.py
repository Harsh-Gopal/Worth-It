import asyncio
import httpx

async def main():
    url = "https://www.swiggy.com/stores/instamart/item/F9UK3KLPCI"
    headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Accept-Encoding": "gzip, deflate, br",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        print("Status:", resp.status_code)
        print("Content-Encoding:", resp.headers.get("Content-Encoding"))
        print("Is text?", resp.text[:50].isascii())

if __name__ == "__main__":
    asyncio.run(main())
