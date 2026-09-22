import asyncio
from app.platforms.swiggy import SwiggyClient

async def main():
    client = SwiggyClient()
    res = await client.resolve_store(25.6075, 85.0830)
    print("Resolved Store:", res)

if __name__ == "__main__":
    asyncio.run(main())
