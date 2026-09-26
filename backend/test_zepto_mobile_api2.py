import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        urls = [
            "https://api.zepto.co.in/user-search-service/api/v3/search",
            "https://api.zepto.co.in/api/v3/search",
            "https://api.zepto.co.in/search"
        ]
        for u in urls:
            try:
                resp = await client.post(u, json={"query": "protein"}, timeout=3)
                print(u, resp.status_code, resp.text[:100])
            except Exception as e:
                print(u, e)

asyncio.run(main())
