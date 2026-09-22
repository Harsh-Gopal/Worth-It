import asyncio
import httpx

async def test_stream():
    url = "http://127.0.0.1:8000/api/search/stream?keywords=Coconut&lat=25.5952&lng=85.0831&radius_km=10&"
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("GET", url) as response:
                print("Connected! Status:", response.status_code)
                async for line in response.aiter_lines():
                    if line:
                        print("SSE:", line)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_stream())
