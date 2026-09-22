import asyncio
from app.scheduler import _run_all_active_alerts
async def main():
    await _run_all_active_alerts()
asyncio.run(main())
