import asyncio
import json
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
        
        reqs = []
        page.on("response", lambda r: reqs.append(r) if "api" in r.url or "graphql" in r.url else None)
        
        await page.goto("https://www.swiggy.com/instamart", wait_until="networkidle", timeout=60000)
        
        for r in reqs:
            try:
                body = await r.text()
                if "storeId" in body or "store_id" in body:
                    print(f"FOUND storeId in {r.url}")
                    # print snippet
                    idx = body.find("storeId")
                    if idx == -1: idx = body.find("store_id")
                    print(body[max(0, idx-50):min(len(body), idx+100)])
            except:
                pass
                
        await browser.close()

asyncio.run(test())
