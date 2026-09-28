import asyncio
import json
from app.core.browser import BrowserManager

async def run():
    opts = {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0"
    }
    
    async with BrowserManager.get_page(context_options=opts) as page:
        await page.context.add_cookies([{
            "name": "userLocation",
            "value": "%7B%22lat%22%3A%2030.7046%2C%20%22lng%22%3A%2076.7179%2C%20%22address%22%3A%20%22India%22%7D",
            "domain": ".swiggy.com",
            "path": "/"
        }])
        
        # Navigate to domain first to establish context
        print("Navigating to Swiggy...")
        await page.goto("https://www.swiggy.com/instamart")
        
        print("Making API request...")
        body = {
            "facets": [],
            "sortAttribute": "",
            "query": "Oats",
            "search_results_offset": "0",
            "page_type": "INSTAMART_SEARCH_PAGE",
            "is_pre_search_tag": False
        }
        
        resp = await page.request.post(
            "https://www.swiggy.com/api/instamart/search/v2?offset=0&ageConsent=false&voiceSearchTrackingId=&storeId=1403831&primaryStoreId=1403831&secondaryStoreId=",
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://www.swiggy.com",
                "Referer": "https://www.swiggy.com/instamart"
            }
        )
        
        print("Status:", resp.status)
        text = await resp.text()
        print("Body preview:", text[:200])
        
        if text:
            with open("playwright_api_resp.json", "w") as f:
                f.write(text)

asyncio.run(run())
