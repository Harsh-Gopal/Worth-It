import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    print("Testing Flipkart fetch request interception...")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        # Dhanaut/Patna
        lat, lng = 25.6012, 85.0697
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            viewport={"width": 1920, "height": 1080},
            geolocation={"longitude": lng, "latitude": lat},
            permissions=["geolocation"],
        )
        page = await context.new_page()
        
        requests_info = []
        
        async def handle_request(request):
            if "api/4/page/fetch" in request.url:
                try:
                    post_data = request.post_data
                    headers = request.headers
                    requests_info.append({
                        "url": request.url,
                        "method": request.method,
                        "headers": headers,
                        "post_data": post_data
                    })
                    print(f"Captured request: {request.url}")
                except Exception:
                    pass

        page.on("request", handle_request)
        
        url = "https://www.flipkart.com/search?q=protein&marketplace=HYPERLOCAL"
        print(f"Navigating to {url}...")
        await page.goto(url)
        
        try:
            await page.wait_for_timeout(3000)
            loc_btns = await page.locator("text=/Use my current location/i").all()
            if loc_btns:
                print("Clicking Use my current location...")
                await loc_btns[0].click(timeout=5000)
                await page.wait_for_url(lambda u: "preview-page" not in u, timeout=15000)
                await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Location error: {e}")
            
        with open("flipkart_requests.json", "w") as f:
            json.dump(requests_info, f, indent=2)
        print("Saved requests to flipkart_requests.json")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
