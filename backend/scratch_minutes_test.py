import asyncio
from app.platforms.flipkart import FlipkartMinutesClient
from app.core.browser import BrowserManager
import logging

logging.basicConfig(level=logging.INFO)

async def test_minutes():
    client = FlipkartMinutesClient()
    try:
        res = await client.resolve_store(25.5941, 85.1376)
        print("RESULT:", res)
    finally:
        await BrowserManager.close()

asyncio.run(test_minutes())
