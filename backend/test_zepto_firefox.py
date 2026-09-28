import asyncio
import json
from urllib.parse import quote, unquote

async def run():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
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
        
        print("Navigating with Firefox...")
        await page.goto("https://www.zeptonow.com/", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(2)
        
        cookies = await context.cookies()
        cookie_names = [c["name"] for c in cookies]
        print("Cookies found:", cookie_names)
        
        service = next((c for c in cookies if c["name"] == "serviceability"), None)
        if service:
            print("Serviceability found!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
