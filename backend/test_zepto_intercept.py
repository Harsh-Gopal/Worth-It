import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def main():
    print("Testing Zepto interception...")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        async def handle_response(response):
            if "api/v3/search" in response.url and "filters" not in response.url:
                print(f"Captured search response from: {response.url}")
                try:
                    data = await response.json()
                    with open("zepto_search_response.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print("Saved to zepto_search_response.json")
                except Exception as e:
                    print(f"Failed to dump response: {e}")

        page.on("response", handle_response)
        
        print("Navigating to Zepto...")
        await page.goto("https://www.zepto.com/")
        
        await context.add_cookies([
            {"name": "isServiceable", "value": "true", "domain": ".zepto.com", "path": "/"},
            {"name": "serviceability", "value": "%7B%22isServiceable%22%3Atrue%2C%22storeId%22%3A%225ec071fd-78df-41f6-b3ae-7298d9f96a3d%22%2C%22storeIds%22%3A%5B%225ec071fd-78df-41f6-b3ae-7298d9f96a3d%22%2C%2227d825a1-77a8-4cfb-b5d3-8968940df2bf%22%2C%22e3ebc54a-a1da-45c1-90bd-1c9f4d4408ec%22%5D%7D", "domain": ".zepto.com", "path": "/"}
        ])
        
        print("Searching for protein...")
        await page.goto("https://www.zepto.com/search?query=protein")
        
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
            
        await asyncio.sleep(2)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
