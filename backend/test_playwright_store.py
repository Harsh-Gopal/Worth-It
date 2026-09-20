import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import json

async def main():
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent=USER_AGENT, viewport={"width": 1440, "height": 900})
        await context.add_cookies([
            {
                "name": "userLocation",
                "value": urllib.parse.quote('{"lat":25.6075768,"lng":85.083029,"address":"India"}'),
                "domain": ".swiggy.com",
                "path": "/"
            }
        ])
        page = await context.new_page()
        await page.goto("https://www.swiggy.com/instamart", wait_until="networkidle")
        
        # Dump localStorage
        ls = await page.evaluate("() => JSON.stringify(localStorage)")
        ls_dict = json.loads(ls)
        print("LOCAL STORAGE KEYS:", ls_dict.keys())
        
        # Look for storeId
        for k, v in ls_dict.items():
            if "store" in k.lower() or "storeId" in v:
                print(f"Key: {k} -> {v[:200]}")
        
        # Also check window.__INITIAL_STATE__
        try:
            state = await page.evaluate("() => window.__INITIAL_STATE__ ? Object.keys(window.__INITIAL_STATE__) : []")
            print("INITIAL STATE KEYS:", state)
            store_id = await page.evaluate("() => window.__INITIAL_STATE__?.storeDetailsV2?.storeId")
            print("STORE ID FROM INITIAL STATE:", store_id)
        except Exception as e:
            print("Error evaluating state:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
