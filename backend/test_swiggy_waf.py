import asyncio
from app.platforms.swiggy import _waf_session
from curl_cffi.requests import AsyncSession

async def run():
    # 1. Get WAF token using Playwright
    await _waf_session.ensure(30.7046, 76.7179)
    print("WAF Ready:", _waf_session.ready)
    print("Device ID:", _waf_session.device_id)
    print("Cookies:", _waf_session.cookies)
    
    # 2. Use curl_cffi to bypass TLS fingerprinting
    sid = "1403831"
    url = f"https://www.swiggy.com/api/instamart/search/v3?offset=0&ageConsent=false&voiceSearchTrackingId=&storeId={sid}&primaryStoreId={sid}&secondaryStoreId="
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-IN,en;q=0.9",
        "content-type": "application/json",
        "x-build-version": "2.367.0",
        "Origin": "https://www.swiggy.com",
        "Referer": "https://www.swiggy.com/instamart",
    }
    if _waf_session.device_id:
        headers["x-device-id"] = _waf_session.device_id
        
    body = {
        "facets": [],
        "sortAttribute": "",
        "query": "Oats",
        "search_results_offset": "0",
        "page_type": "INSTAMART_SEARCH_PAGE",
        "is_pre_search_tag": False,
    }
    
    async with AsyncSession(impersonate="chrome120") as s:
        # add cookies
        for k, v in _waf_session.cookies.items():
            s.cookies.set(k, v, domain=".swiggy.com")
            
        r = await s.post(url, headers=headers, json=body)
        print("Status:", r.status_code)
        print("Body preview:", r.text[:300])
        if "data" in r.text:
            print("SUCCESS! Data found!")
        else:
            print("FAILED.")

asyncio.run(run())
