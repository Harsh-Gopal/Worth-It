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
        
        print("Navigating to Swiggy...")
        await page.goto("https://www.swiggy.com/instamart", wait_until="networkidle")
        
        print("Making fetch request via evaluate...")
        
        # We need the storeId. We can fetch it first if we want, or just use 1403831.
        js_fetch = """
        async () => {
            const body = {
                "facets": [],
                "sortAttribute": "",
                "query": "Oats",
                "search_results_offset": "0",
                "page_type": "INSTAMART_SEARCH_PAGE",
                "is_pre_search_tag": false
            };
            const response = await fetch('/api/instamart/search/v2?offset=0&ageConsent=false&voiceSearchTrackingId=&storeId=1403831&primaryStoreId=1403831&secondaryStoreId=', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(body)
            });
            const text = await response.text();
            return {status: response.status, text: text};
        }
        """
        
        result = await page.evaluate(js_fetch)
        
        print("Status:", result['status'])
        print("Body preview:", result['text'][:200])
        
        if result['text']:
            with open("evaluate_api_resp.json", "w") as f:
                f.write(result['text'])

asyncio.run(run())
