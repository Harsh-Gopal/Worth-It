import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0"
        )
        await context.add_cookies([
            {
                "name": "userLocation",
                "value": urllib.parse.quote('{"lat":12.9716,"lng":77.5946,"address":"Bangalore"}'),
                "domain": ".swiggy.com",
                "path": "/"
            }
        ])
        page = await context.new_page()
        
        api_calls = []
        async def log_request(route):
            req = route.request
            if "api/instamart" in req.url:
                api_calls.append(req.url)
            await route.continue_()
            
        await page.route("**/*", log_request)
        
        print("Navigating...")
        await page.goto("https://www.swiggy.com/instamart", wait_until="networkidle")
        
        print(f"API calls intercepted: {len(api_calls)}")
        for call in api_calls:
            print(call)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
