import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Use headless=True, but pass the flag for new headless mode
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--headless=new",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        # hide webdriver
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Navigating...")
        response = await page.goto("https://www.zepto.com/search?q=protein", wait_until="domcontentloaded")
        print("Status:", response.status)
        await page.wait_for_timeout(3000)
        content = await page.content()
        print("Length:", len(content))
        
        if "product-card" in content:
            print("FOUND PRODUCTS!")
        else:
            print("NO PRODUCTS.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
