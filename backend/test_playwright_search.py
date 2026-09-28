import asyncio
import json
from app.core.browser import BrowserManager

async def run():
    opts = {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0"
    }
    
    search_data = None
    
    async def log_response(response):
        nonlocal search_data
        if "api/instamart/search" in response.url or "graphql" in response.url:
            if response.status == 200:
                try:
                    text = await response.text()
                    if text:
                        data = json.loads(text)
                        if "data" in data and ("widgets" in data["data"] or "cards" in data["data"]):
                            search_data = data
                            print(f"Captured SEARCH DATA from {response.url}!")
                except Exception as e:
                    pass

    async with BrowserManager.get_page(context_options=opts) as page:
        await page.context.add_cookies([{
            "name": "userLocation",
            "value": "%7B%22lat%22%3A%2030.7046%2C%20%22lng%22%3A%2076.7179%2C%20%22address%22%3A%20%22India%22%7D",
            "domain": ".swiggy.com",
            "path": "/"
        }])
        
        page.on("response", log_response)
        
        print("Navigating to Swiggy search...")
        await page.goto("https://www.swiggy.com/instamart/search?query=Oats", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        if search_data:
            with open("swiggy_search_response.json", "w") as f:
                json.dump(search_data, f, indent=2)
            print("Saved to swiggy_search_response.json")
        else:
            print("No search response captured.")

asyncio.run(run())
