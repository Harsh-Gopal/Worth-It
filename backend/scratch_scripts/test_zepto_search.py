import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Navigating to zeptonow.com...")
        await page.goto("https://www.zeptonow.com/", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # intercept responses
        async def handle_response(response):
            if "search" in response.url.lower():
                print(f"SEARCH RESPONSE: {response.url} {response.status}")
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(json.dumps(data, indent=2)[:500])
                    except:
                        pass
        
        page.on("response", handle_response)
        
        print("Searching for whey...")
        await page.fill('input[placeholder*="Search"]', "whey")
        await page.keyboard.press("Enter")
        
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
