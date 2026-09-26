import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"
        )
        page = await context.new_page()
        
        # Open Flipkart Minutes
        print("Navigating to Minutes...")
        await page.goto("https://www.flipkart.com/minutes")
        
        try:
            # Wait for location banner and click "Use my current location"
            print("Clicking Use my current location")
            await page.wait_for_selector("text=Use my current location", timeout=10000)
            await page.click("text=Use my current location")
            await page.wait_for_timeout(2000)  # Wait for it to apply
        except Exception as e:
            print("Could not click location:", e)

        print("Taking minutes_home.png")
        await page.screenshot(path="minutes_home.png")

        url = "https://www.flipkart.com/amul-gold-homogenised-standardised-milk/p/itme3a8cf822f3c0?pid=MLKGCZCWBYA8FDB4&marketplace=HYPERLOCAL"
        print("Navigating to product:", url)
        await page.goto(url)
        
        try:
            await page.wait_for_url("**/product/**", timeout=10000)
        except:
            pass
        
        print("Final URL:", page.url)
        
        print("Taking minutes_product.png")
        await page.screenshot(path="minutes_product.png")
        
        html = page.content()
        with open("flipkart_dump2.html", "w") as f:
            f.write(html)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
