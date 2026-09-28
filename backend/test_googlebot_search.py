import asyncio
import httpx
import re
import json

async def run():
    headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"
    }
    cookies = {
        "userLocation": "%7B%22lat%22%3A%2030.7046%2C%20%22lng%22%3A%2076.7179%2C%20%22address%22%3A%20%22India%22%7D"
    }
    async with httpx.AsyncClient() as client:
        r = await client.get("https://www.swiggy.com/instamart/search?custom_back=true&query=Oats", headers=headers, cookies=cookies)
        print("Status:", r.status_code)
        
        html = r.text
        match = re.search(r"window\.initialState\s*=\s*(\{.*?\});", html, re.DOTALL)
        if match:
            state = json.loads(match.group(1))
            print("Found initialState! Keys:", state.keys())
            
            with open("googlebot_search_state.json", "w") as f:
                json.dump(state, f, indent=2)
            print("Saved to googlebot_search_state.json")
        else:
            print("Could not find window.initialState")

asyncio.run(run())
