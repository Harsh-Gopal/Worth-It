import asyncio
from app.core.browser import BrowserManager

async def run():
    opts = {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0"
    }
    
    async with BrowserManager.get_page(context_options=opts) as page:
        await page.goto("https://www.swiggy.com/instamart")
        await page.wait_for_timeout(5000)
        cookies = await page.context.cookies()
        for c in cookies:
            print(f"Cookie: {c['name']} = {c['value'][:20]}...")

asyncio.run(run())
