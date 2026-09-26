import asyncio
from playwright.async_api import async_playwright

async def test_browser(browser_type_name):
    async with async_playwright() as p:
        browser_type = getattr(p, browser_type_name)
        browser = await browser_type.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        print(f"[{browser_type_name}] Navigating...")
        response = await page.goto("https://www.zepto.com/search?q=protein", wait_until="domcontentloaded", timeout=15000)
        print(f"[{browser_type_name}] Status:", response.status)
        
        await page.wait_for_timeout(3000)
        content = await page.content()
        print(f"[{browser_type_name}] Length:", len(content))
        
        if "product-card" in content or "Let's Try" in content:
            print(f"[{browser_type_name}] FOUND PRODUCTS!")
        else:
            print(f"[{browser_type_name}] NO PRODUCTS.")

        await browser.close()

async def main():
    for b in ['firefox', 'webkit']:
        try:
            await test_browser(b)
        except Exception as e:
            print(f"[{b}] Failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
