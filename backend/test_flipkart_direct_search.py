import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    print("Testing direct search...")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        lat, lng = 25.6012, 85.0697
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            viewport={"width": 1920, "height": 1080},
            geolocation={"longitude": lng, "latitude": lat},
            permissions=["geolocation"],
        )
        page = await context.new_page()
        
        found_products = []
        async def handle_response(response):
            if "api/4/page/fetch" in response.url:
                try:
                    data = await response.json()
                    slots = data.get("RESPONSE", {}).get("slots", [])
                    for slot in slots:
                        widget = slot.get("widget", {})
                        if widget.get("type") == "PRODUCT_SUMMARY_EXTENDED":
                            for prod in widget.get("data", {}).get("products", []):
                                val = prod.get("productInfo", {}).get("value", {})
                                name = val.get("titles", {}).get("title")
                                found_products.append(name)
                except Exception:
                    pass

        page.on("response", handle_response)
        
        url = "https://www.flipkart.com/search?q=protein&marketplace=HYPERLOCAL"
        print(f"Navigating to {url}...")
        await page.goto(url)
        await page.wait_for_timeout(5000)
        
        print("Products found (direct):", found_products)
        
        # If no products, try clicking the button
        if not found_products:
            loc_btns = await page.locator("text=/Use my current location/i").all()
            if loc_btns:
                print("Clicking Use my current location...")
                await loc_btns[0].click(timeout=5000)
                await page.wait_for_url(lambda u: "preview-page" not in u, timeout=15000)
                await page.wait_for_timeout(3000)
                print("Products found (after click):", found_products)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
