import asyncio
from curl_cffi.requests import AsyncSession

async def run():
    async with AsyncSession(impersonate="chrome120") as s:
        sid = "1403831"
        url = f"https://www.swiggy.com/api/instamart/search/v2?offset=0&query=Oats&storeId={sid}&primaryStoreId={sid}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-IN,en;q=0.9",
            "Origin": "https://www.swiggy.com",
            "Referer": "https://www.swiggy.com/instamart",
        }
        
        print("Testing GET...")
        r = await s.get(url, headers=headers)
        print("Status:", r.status_code)
        print("Body preview:", r.text[:200])

asyncio.run(run())
