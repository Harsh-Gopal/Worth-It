import asyncio
import uuid
from app.platforms.swiggy import _waf_session, _get_shared_client
import httpx

async def run():
    print("Ensuring WAF session...")
    await _waf_session.ensure(30.7046, 76.7179)
    
    sid = "1403831"
    url = f"https://www.swiggy.com/api/instamart/search/v2?offset=0&ageConsent=false&voiceSearchTrackingId=&storeId={sid}&primaryStoreId={sid}&secondaryStoreId="
    
    device_id = str(uuid.uuid4())
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "x-device-id": device_id,
        "Origin": "https://www.swiggy.com",
        "Referer": "https://www.swiggy.com/instamart",
    }
    
    body = {
        "facets": [],
        "sortAttribute": "",
        "query": "Oats",
        "search_results_offset": "0",
        "page_type": "INSTAMART_SEARCH_PAGE",
        "is_pre_search_tag": False
    }
    
    client = _get_shared_client()
    print(f"Making request with x-device-id: {device_id}")
    resp = await client.post(url, headers=headers, json=body, cookies=_waf_session.cookies, timeout=httpx.Timeout(30.0))
    print(f"Status: {resp.status_code}")
    print(f"Body snippet: {resp.text[:200]}")

asyncio.run(run())
