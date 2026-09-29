import asyncio
from app.notifications.telegram import TelegramNotificationProvider
import httpx
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    async with httpx.AsyncClient() as client:
        provider = TelegramNotificationProvider(client)
        res = await provider.notify("test", "test message")
        print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
