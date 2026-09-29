import asyncio
from app.platforms.blinkit import BlinkitClient

async def main():
    client = BlinkitClient()
    res = await client.product_at_store("2858", "1394450", 12.9716, 77.5946) # Let's say prid 2858
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
