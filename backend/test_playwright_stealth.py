import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--headless=new", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print("Navigating with playwright-stealth...")
        response = await page.goto("https://www.zepto.com/search?q=protein", wait_until="domcontentloaded", timeout=15000)
        print("Status:", response.status)
        
        # Wait a bit to let any JS redirects or challenges complete
        await page.wait_for_timeout(4000)
        
        content = await page.content()
        print("Length:", len(content))
        
        if "product-card" in content or "Let's Try" in content:
            print("FOUND PRODUCTS!")
        else:
            print("NO PRODUCTS.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
