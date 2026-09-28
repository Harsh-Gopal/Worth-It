import asyncio
import json
from urllib.parse import quote, unquote

async def run():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        lat = 30.7046
        lng = 76.7179
        position = quote(json.dumps({"latitude": lat, "longitude": lng}, separators=(",", ":")), safe="")
        
        for domain in [".zeptonow.com", ".zepto.com"]:
            await context.add_cookies([{
                "name": "user_position",
                "value": position,
                "domain": domain,
                "path": "/"
            }])
        
        print("Navigating...")
        await page.goto("https://www.zeptonow.com/", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        
        content = await page.content()
        with open("zepto_page.html", "w") as f:
            f.write(content)
            
        local_storage = await page.evaluate("() => JSON.stringify(localStorage)")
        print("LocalStorage keys:", json.loads(local_storage).keys())
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
