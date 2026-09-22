import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Resolve Patna 800014
        url = "http://127.0.0.1:8000/api/location/resolve?address=800014"
        res = await client.get(url)
        print("RESOLVE:", res.json())

if __name__ == "__main__":
    asyncio.run(main())
