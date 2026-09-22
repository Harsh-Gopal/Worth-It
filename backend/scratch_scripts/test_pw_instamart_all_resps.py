import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
            locale="en-IN", timezone_id="Asia/Kolkata"
        )
        await context.add_cookies([
            {"name": "userLocation", "value": urllib.parse.quote('{"lat":25.6075,"lng":85.0830,"address":"India"}'), "domain": ".swiggy.com", "path": "/"}
        ])
        page = await context.new_page()
        
        resps = []
        page.on("response", lambda r: resps.append(r))
        
        await page.goto("https://www.swiggy.com/instamart", wait_until="networkidle", timeout=60000)
        
        for r in resps:
            try:
                body = await r.text()
                if "1401272" in body:
                    print("FOUND in Response body of:", r.url)
            except:
                pass
                
        await browser.close()

asyncio.run(test())
