import asyncio
import httpx
import re
import json

async def test_search_web():
    url = "https://www.swiggy.com/instamart/search?custom_back=true&query=coconut"
    headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Cookie": "userLocation=%7B%22lat%22%3A25.6075768%2C%22lng%22%3A85.083029%2C%22address%22%3A%22India%22%7D",
    }
    
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        print("Status:", resp.status_code)
        
        # Look for Redux state
        match = re.search(r'window\.initialState\s*=\s*(\{.*?\});', resp.text)
        if match:
            print("Found Redux state!")
            state = json.loads(match.group(1))
            print(state.keys())
        else:
            print("No Redux state found.")
            # Print title
            title = re.search(r'<title>(.*?)</title>', resp.text)
            if title:
                print("Title:", title.group(1))
            if "Just a moment" in resp.text or "Cloudflare" in resp.text:
                print("Blocked by WAF!")
                
asyncio.run(test_search_web())
