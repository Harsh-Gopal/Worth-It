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
            
        async def on_response(response):
            if "store" in response.url.lower() or "location" in response.url.lower() or "tenant" in response.url.lower():
                print(f"API: {response.url} - Status: {response.status}")
                if response.status == 200:
                    try:
                        data = await response.json()
                        print("Data:", json.dumps(data)[:200])
                    except Exception:
                        pass
        
        page.on("response", on_response)
        
        print("Navigating...")
        await page.goto("https://www.zeptonow.com/", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
