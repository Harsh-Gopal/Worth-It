import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", "http://127.0.0.1:8000/api/search/stream?keywords=Coconut&radius_km=5&lat=25.6075&lng=85.0830&require_in_stock=true") as response:
            async for line in response.aiter_lines():
                print(line)

asyncio.run(main())
