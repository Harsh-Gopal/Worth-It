import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            geolocation={"latitude": 25.6012, "longitude": 85.0697},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()
        
        url = "https://www.flipkart.com/product/p/itme?pid=itme3a8cf822f3c0&marketplace=HYPERLOCAL"
        print("Navigating...")
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(4000)
        
        # Click GPS
        loc_btns = await page.locator("text=/Use my current location/i").all()
        if loc_btns:
            print("Clicking Use my current location")
            await loc_btns[0].click()
            try:
                await page.wait_for_url(lambda u: "hyperlocal-preview-page" not in u, timeout=12000)
            except Exception:
                print("Failed to navigate away from preview page")
            
        print("Final URL:", page.url)
        # wait 5s for react to render
        await page.wait_for_timeout(5000)
        content = await page.content()
        with open("flipkart_dump.html", "w") as f:
            f.write(content)
            
        await browser.close()
        print("Done dumping to flipkart_dump.html")

if __name__ == "__main__":
    asyncio.run(main())
