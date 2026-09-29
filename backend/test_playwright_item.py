import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.swiggy.com/instamart/item/8ILS98WFQR", wait_until="networkidle")
        print("Final URL:", page.url)
        print("Title:", await page.title())
        content = await page.content()
        print("Contains productV2:", "productV2" in content)
        print("storeDetailsV2 null:", '"storeDetailsV2":null' in content)
        await browser.close()

asyncio.run(main())
