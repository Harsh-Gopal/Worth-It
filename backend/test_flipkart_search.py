import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 800014
        lat, lng = 25.5941, 85.1376
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            geolocation={"latitude": lat, "longitude": lng},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()
        
        # Navigate to a minutes URL first to set the location
        url = "https://www.flipkart.com/search?q=Sports+%26+Fitness&marketplace=HYPERLOCAL"
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        loc_btns = await page.locator("text=/Use my current location/i").all()
        if loc_btns:
            print("Clicking location button...")
            await loc_btns[0].click(timeout=5000)
            await page.wait_for_timeout(5000)
        
        content = await page.content()
        # Find product cards
        items = await page.locator("a[href*='/p/']").all()
        print(f"Found {len(items)} product links")
        
        titles = await page.locator("div.KzDlHZ, a[class*='WKTcLC'], a[class*='IRpwTa'], div[class*='s1Q9rs']").all_inner_texts()
        print("Titles:", titles)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
