import asyncio
from app.platforms.flipkart import FlipkartMinutesClient

async def main():
    client = FlipkartMinutesClient()
    print("Resolving store...")
    # Bangalore: 12.9259, 77.6253
    res = await client.resolve_store(lat=12.9259, lng=77.6253)
    print("Store:", res)
    if res.store_id:
        print("Searching...")
        search_res = await client.search("FIAMA", res.store_id, lat=12.9259, lng=77.6253)
        print("Result:", len(search_res), search_res)
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
