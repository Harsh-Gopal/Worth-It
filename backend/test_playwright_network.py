import asyncio
import json
from playwright.async_api import async_playwright
from app.platforms.swiggy import _waf_session, _make_location_cookie

async def main():
    await _waf_session.ensure(12.9716, 77.6411)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        # Add the WAF cookies
        cookies = []
        for k, v in _waf_session.cookies.items():
            cookies.append({"name": k, "value": str(v), "domain": ".swiggy.com", "path": "/"})
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # Monitor network
        apis_called = []
        page.on("request", lambda req: apis_called.append(req.url) if "api" in req.url else None)
        
        await page.goto("https://www.swiggy.com/instamart/item/8ILS98WFQR", wait_until="networkidle")
        print("Final URL:", page.url)
        print("Title:", await page.title())
        
        for url in apis_called:
            if "graphql" in url or "item" in url or "product" in url:
                print("Interesting API Call:", url)
                
        await browser.close()

asyncio.run(main())
