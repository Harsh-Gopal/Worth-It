import asyncio
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
        
        async def log_response(response):
            if "search" in response.url.lower():
                print(f"SEARCH RESP: {response.url} (Status: {response.status})")
                
        page.on("response", log_response)
        
        print("Navigating to Swiggy instamart...")
        await page.goto("https://www.swiggy.com/instamart")
        await page.wait_for_timeout(2000)
        
        print("Navigating to search page...")
        await page.goto("https://www.swiggy.com/instamart/search")
        await page.wait_for_timeout(2000)
        
        print("Typing Oats...")
        await page.fill("input[type='text']", "Oats")
        await page.wait_for_timeout(3000)
        
        html = await page.content()
        with open("swiggy_dom.html", "w") as f:
            f.write(html)
        print("Saved DOM to swiggy_dom.html")

asyncio.run(run())
