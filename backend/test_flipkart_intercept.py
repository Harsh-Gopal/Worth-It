import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    print("Testing Flipkart interception...")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        # Dhanaut/Patna or Bangalore coordinates
        lat, lng = 12.9716, 77.5946
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            viewport={"width": 1920, "height": 1080},
            geolocation={"longitude": lng, "latitude": lat},
            permissions=["geolocation"],
        )
        page = await context.new_page()
        
        api_responses = []
        
        async def handle_response(response):
            if "api/4/page/fetch" in response.url:
                print(f"Captured response from: {response.url}")
                try:
                    data = await response.json()
                    with open("flipkart_fetch_response.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print("Saved to flipkart_fetch_response.json")
                    api_responses.append(data)
                except Exception as e:
                    print("Could not parse JSON:", e)

        page.on("response", handle_response)
        
        # Test product: Amul Taaza
        # Let's use a known PID. If not, just search for something or use a dummy.
        # Wait, I don't have a known PID off the top of my head. Let's use the one from search?
        # Let's search first or just use a generic product link. 
        # Actually, let's navigate to the main Flipkart Minutes page first, then search? 
        # Or just use the homepage. 
        print("Navigating to Flipkart Minutes...")
        await page.goto("https://www.flipkart.com/hyperlocal-preview-page?marketplace=HYPERLOCAL")
        
        try:
            await page.wait_for_timeout(3000)
            loc_btns = await page.locator("text=/Use my current location/i").all()
            if loc_btns:
                print("Clicking Use my current location...")
                await loc_btns[0].click(timeout=5000)
                await page.wait_for_timeout(3000)
        except Exception as e:
            print("Location click error:", e)
            
        print("Searching for protein on Flipkart Minutes...")
        await page.goto("https://www.flipkart.com/search?q=protein&marketplace=HYPERLOCAL")
        
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
            
        await asyncio.sleep(2)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
