import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            geolocation={"latitude": 12.9259, "longitude": 77.6253},
            permissions=["geolocation"],
        )
        page = await ctx.new_page()
        # Navigate to a generic minutes product to set location
        await page.goto("https://www.flipkart.com/product/p/itme?pid=SNCGTVXZGFGGYGZJ&marketplace=HYPERLOCAL", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        loc_btns = await page.locator("text=/Use my current location/i").all()
        if loc_btns:
            await loc_btns[0].click()
            await page.wait_for_timeout(4000)
        
        await page.goto("https://www.flipkart.com/search?q=fiama&marketplace=HYPERLOCAL")
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="flipkart_search.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
