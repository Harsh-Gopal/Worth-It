import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        urls = [
            "https://api.zeptonow.com/api/v1/search?query=protein",
            "https://api.zeptonow.com/v1/search?query=protein",
            "https://api.zeptonow.com/v3/search?query=protein",
            "https://api.zepto.co.in/api/v1/search?query=protein",
            "https://api.zepto.co.in/v1/search?query=protein"
        ]
        for u in urls:
            try:
                resp = await client.get(u, timeout=3)
                print(u, resp.status_code)
            except Exception as e:
                print(u, e)

asyncio.run(main())
