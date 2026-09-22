import asyncio
import httpx
import urllib.parse
from playwright.async_api import async_playwright

async def get_waf_cookies(lat, lng):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
            locale="en-IN", timezone_id="Asia/Kolkata"
        )
        await context.add_cookies([
            {"name": "userLocation", "value": urllib.parse.quote(f'{{"lat":{lat},"lng":{lng},"address":"India"}}'), "domain": ".swiggy.com", "path": "/"}
        ])
        page = await context.new_page()
        await page.goto("https://www.swiggy.com/instamart", wait_until="domcontentloaded", timeout=60000)
        
        for _ in range(30):
            cookies = await context.cookies()
            cnames = [c["name"] for c in cookies]
            if "aws-waf-token" in cnames and "deviceId" in cnames:
                break
            await asyncio.sleep(1)
        final_cookies = {c["name"]: c["value"] for c in await context.cookies()}
        await browser.close()
        return final_cookies

async def search_with_cookies(keyword, store_id, cookies):
    url = f"https://www.swiggy.com/api/instamart/search/v2?offset=0&ageConsent=false&storeId={store_id}&primaryStoreId={store_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
        "content-type": "application/json",
        "x-device-id": urllib.parse.unquote(cookies.get("deviceId", "")).removeprefix("s:").split(".")[0],
    }
    body = {
        "facets": [], "sortAttribute": "", "query": keyword, "search_results_offset": "0", "page_type": "INSTAMART_SEARCH_PAGE"
    }
    async with httpx.AsyncClient(timeout=10.0, cookies=cookies) as client:
        resp = await client.post(url, headers=headers, json=body)
        print(f"Store {store_id} -> {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            items = []
            for card in ((data.get("data") or {}).get("cards") or []):
                grid = (((card.get("card") or {}).get("card") or {}).get("gridElements") or {}).get("infoWithStyle") or {}
                for item in grid.get("items") or []:
                    for v in item.get("variations") or []:
                        items.append(v.get("displayName", ""))
            print(f"  Found {len(items)} items")

async def test():
    cookies = await get_waf_cookies(25.6075, 85.0830)
    print("Got cookies:", len(cookies))
    
    # Try different store IDs
    stores = ["", "synthetic_25.61_85.08", "synthetic_25.61_85.09", "synthetic_25.60_85.07", "synthetic_25.62_85.06"]
    
    tasks = [search_with_cookies("Coconut", s, cookies) for s in stores]
    await asyncio.gather(*tasks)

asyncio.run(test())
