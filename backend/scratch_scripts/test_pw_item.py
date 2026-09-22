import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import json

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
            locale="en-IN", timezone_id="Asia/Kolkata"
        )
        val = urllib.parse.quote('{"lat":25.6075,"lng":85.0830,"address":"India"}')
        await context.add_cookies([
            {"name": "userLocation", "value": val, "domain": ".swiggy.com", "path": "/"}
        ])
        page = await context.new_page()
        await page.goto("https://www.swiggy.com/instamart/item/CYXCSXYK4T", wait_until="networkidle", timeout=60000)
        html = await page.content()
        
        # Search for CYXCSXYK4T
        idx = html.find("CYXCSXYK4T")
        if idx != -1:
            print("FOUND CYXCSXYK4T in HTML!")
            print(html[max(0, idx-100):min(len(html), idx+100)])
        else:
            print("CYXCSXYK4T NOT FOUND IN HTML")
            
        await browser.close()

asyncio.run(test())
