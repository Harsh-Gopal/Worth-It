import asyncio
import httpx
from app.platforms.swiggy import SwiggyClient

async def main():
    client = SwiggyClient()
    try:
        # Patna probe lat/lng
        res = await client.resolve_store(25.6075, 85.0830)
        print("Store Resolution:", res)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(main())
