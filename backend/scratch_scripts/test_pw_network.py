import asyncio
import json
from playwright.async_api import async_playwright
from app.platforms.swiggy import _make_location_cookie

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
            locale="en-IN", timezone_id="Asia/Kolkata"
        )
        await context.add_cookies([
            {"name": "userLocation", "value": "%7B%22lat%22%3A25.6075%2C%22lng%22%3A85.0830%2C%22address%22%3A%22India%22%7D", "domain": ".swiggy.com", "path": "/"}
        ])
        page = await context.new_page()
        
        requests_seen = []
        page.on("request", lambda request: requests_seen.append(request.url))
        
        await page.goto("https://www.swiggy.com/instamart/item/CYXCSXYK4T", wait_until="networkidle", timeout=60000)
        
        for url in requests_seen:
            if "api" in url or "graphql" in url or "search" in url:
                print(url)
                
        await browser.close()

asyncio.run(test())
