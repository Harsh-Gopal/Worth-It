import asyncio
import sys
import json
import logging
from urllib.parse import quote
sys.path.insert(0, "/Users/harshgopal/code/myprojects/price_drop/Worth-It/backend")

from playwright.async_api import async_playwright
from curl_cffi.requests import AsyncSession

logging.basicConfig(level=logging.DEBUG)

lat, lng = 12.9259, 77.6253

async def main():
    position = quote(json.dumps({"latitude": lat, "longitude": lng}, separators=(",", ":")), safe="")
    
    async with async_playwright() as p:
        # Chrome 120 UA used by curl_cffi
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800}, user_agent=ua)
        for domain in [".zeptonow.com", ".zepto.com"]:
            await context.add_cookies([{"name": "user_position", "value": position, "domain": domain, "path": "/"}])
        
        page = await context.new_page()
        try:
            await page.goto("https://www.zeptonow.com/", wait_until="commit", timeout=20000)
            await page.wait_for_timeout(8000)
        except Exception as e:
            print("goto err:", e)
        
        cookies = await context.cookies()
        cookies_dict = {c["name"]: c["value"] for c in cookies}
        print("Cookies obtained:", list(cookies_dict.keys()))
        
        await browser.close()
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "platform": "WEB",
        "tenant": "ZEPTO",
        "appversion": "17.0.1",
        "app_version": "17.0.1",
        "deviceid": cookies_dict.get("device_id", ""),
        "device_id": cookies_dict.get("device_id", ""),
        "sessionid": cookies_dict.get("session_id", ""),
        "session_id": cookies_dict.get("session_id", ""),
        "x-without-bearer": "true",
        "auth_revamp_flow": "v2",
        "marketplace_type": "SUPER_SAVER",
        "Origin": "https://www.zeptonow.com",
        "Referer": "https://www.zeptonow.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Accept-Language": "en-US,en;q=0.9",
        "x-xsrf-token": cookies_dict.get("XSRF-TOKEN", ""),
        "x-csrf-secret": cookies_dict.get("csrfSecret", ""),
        "compatible_components": "CONVENIENCE_FEE,RAIN_FEE,LATE_NIGHT_FEE,KITCHEN_PREPARATION_FEE,EXTERNAL_COUPONS,COUPON_WIDGET,STANDALONE_COUPON_WIDGET,BILL_SUMMARY_PROMO_WIDGET,BREADCRUMB_WIDGET,WIDGET_L1_L2_CATEGORY_GRID,SEARCH_RECENT_SEARCH_TERMS_WIDGET,NATIVE_BANNERS,SEARCH_TRENDING_TERMS_WIDGET,SEARCH_CATEGORIES_WIDGET,PROMO_BANNERS,SEARCH_BRAND_STORE_WIDGET,WIDGET_SPONSORED_PRODUCTS,SEARCHED_PRODUCTS,SUPER_SAVINGS_WIDGET,BOTTOM_NUDGE_WIDGET,IN_APP_NUDGE_WIDGET,WIDGET_BILL_SAVINGS_NUDGE,WIDGET_BANK_PROMO,RIDER_TIP_WIDGET,SAVINGS_WIDGET,BILL_SUMMARY_WIDGET,WIDGET_SUBSCRIPTION_BENEFITS,WIDGET_ORDER_AGAIN,WIDGET_REORDER_ITEM,WIDGET_CANDIDATE_PRODUCTS,WIDGET_CART_SUGGESTION,WIDGET_USER_BEHAVIOUR_SUGGESTIONS,WIDGET_FAVOURITES_SUGGESTION,DELIVERY_INSTRUCTION_WIDGET,MINIMAL_DELIVERY_INSTRUCTION_WIDGET,WIDGET_DYNAMIC_BILL_NUDGES,WIDGET_PAYMENT_NUDGE_V1,WIDGET_SUB_CATEGORY_SUGGESTION,DELIVERY_LATENCY_WIDGET,WIDGET_ORDER_PROCESSING_NUDGE,WIDGET_ITEM_DETAILS_OFFERS,COUPON_WIDGET_V2",
    }
    
    import urllib.parse
    serviceability_raw = cookies_dict.get("serviceability")
    if not serviceability_raw:
        print("No serviceability cookie")
        return
    data = json.loads(urllib.parse.unquote(serviceability_raw))
    store_id = data.get("primaryStore", {}).get("storeId")
    print("Store ID:", store_id)
    
    headers["storeid"] = store_id
    headers["store_id"] = store_id
    headers["store_ids"] = store_id
    
    body = {
        "query": "protein",
        "pageNumber": 0,
        "mode": "SHOW_ALL_RESULTS",
        "userSessionId": cookies_dict.get("session_id", "test-123")
    }
    
    print("Making request with curl_cffi...")
    async with AsyncSession(impersonate="chrome120") as client:
        resp = await client.post(
            "https://bff-gateway.zepto.com/user-search-service/api/v3/search", 
            headers=headers, 
            json=body,
            cookies=cookies_dict
        )
        print("Status:", resp.status_code)
        if resp.status_code == 200:
            print("SUCCESS! Keys:", list(resp.json().keys()))
        else:
            print("Error body:", resp.text)

asyncio.run(main())
