import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        # Inject stealth script
        import urllib.request
        stealth_js = urllib.request.urlopen("https://raw.githubusercontent.com/berstend/puppeteer-extra/master/packages/puppeteer-extra-plugin-stealth/evasions/webgl.vendor/index.js").read().decode("utf-8")
        # Wait, a full stealth script is better.
        
        page = await context.new_page()
        # hide webdriver
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        await page.add_init_script("window.chrome = { runtime: {} };")
        
        print("Navigating...")
        response = await page.goto("https://www.zepto.com/search?q=protein", wait_until="networkidle")
        print("Status:", response.status)
        content = await page.content()
        print("Length:", len(content))
        
        if "product-card" in content:
            print("FOUND PRODUCTS!")
        else:
            print("NO PRODUCTS.")
            print(content[:500])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
