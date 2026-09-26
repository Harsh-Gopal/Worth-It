import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 800014
        lat, lng = 25.5941, 85.1376
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            geolocation={"latitude": lat, "longitude": lng},
            permissions=["geolocation"]
        )
        page = await ctx.new_page()
        
        url = "https://www.flipkart.com/search?q=Sports+%26+Fitness&marketplace=HYPERLOCAL"
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        loc_btns = await page.locator("text=/Use my current location/i").all()
        if loc_btns:
            await loc_btns[0].click(timeout=5000)
            await page.wait_for_timeout(4000)
            
        # evaluate js to extract items
        js = """() => {
            const results = [];
            const items = document.querySelectorAll("a[href*='/p/']");
            for (const el of items) {
                const href = el.getAttribute('href');
                let name = null;
                const titleEl = el.querySelector("div.KzDlHZ, .s1Q9rs, .wjcEIp");
                if(titleEl) { name = titleEl.innerText; }
                else if (el.hasAttribute('title')) { name = el.getAttribute('title'); }
                
                let price = null;
                const priceEl = el.querySelector("div.Nx9bqj");
                if (priceEl) { price = parseFloat(priceEl.innerText.replace(/[^0-9.]/g, '')); }
                
                let mrp = null;
                const mrpEl = el.querySelector("div.yRaY8j");
                if (mrpEl) { mrp = parseFloat(mrpEl.innerText.replace(/[^0-9.]/g, '')); }
                
                if (name && price && href) {
                    const pidMatch = href.match(/pid=([A-Z0-9]+)/);
                    if (pidMatch) {
                        results.push({
                            id: pidMatch[1],
                            name: name,
                            price: price,
                            mrp: mrp || price
                        });
                    }
                }
            }
            return results;
        }"""
        
        res = await page.evaluate(js)
        print(f"Found {len(res)} results:")
        for r in res:
            print(f"- {r['name']} | Price: {r['price']} | MRP: {r['mrp']} | ID: {r['id']}")
            
        await browser.close()
        
if __name__ == "__main__":
    asyncio.run(main())
