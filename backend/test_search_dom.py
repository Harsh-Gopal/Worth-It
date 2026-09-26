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
        await page.wait_for_timeout(5000)
        
        # Scrape basic product items
        items = await page.evaluate('''() => {
            const results = [];
            // Flipkart Minutes products are often inside links matching "/product/p/" or inside cards
            const links = document.querySelectorAll('a[href*="/p/itm"]');
            for (const a of links) {
                const titleEl = a.querySelector('div[class*="syl9yP"], img');
                const priceEl = a.querySelector('div.Nx9bqj');
                if (priceEl) {
                    results.push({
                        href: a.getAttribute('href'),
                        title: titleEl ? (titleEl.title || titleEl.alt || titleEl.textContent) : null,
                        price: priceEl.textContent,
                        html: a.innerHTML.substring(0, 200)
                    });
                }
            }
            return results;
        }''')
        
        import json
        with open("search_results.json", "w") as f:
            json.dump(items, f, indent=2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
