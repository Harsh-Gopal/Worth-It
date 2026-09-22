import asyncio
import httpx

async def test_search():
    store_id = "1394450"
    query = "coconut"
    url = "https://www.swiggy.com/api/instamart/search/v2"
    
    headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Accept": "*/*",
        "Accept-Language": "en-IN,en;q=0.9",
        "content-type": "application/json",
        "Origin": "https://www.swiggy.com",
        "Referer": "https://www.swiggy.com/instamart",
    }
    
    params = {
        "offset": 0,
        "storeId": store_id,
        "primaryStoreId": store_id,
    }
    
    json_data = {
        "facets": [],
        "sortAttribute": "",
        "query": query,
        "search_results_offset": "0",
        "page_type": "INSTAMART_SEARCH_PAGE",
        "is_pre_search_tag": False
    }
    
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.post(url, headers=headers, params=params, json=json_data)
        print("Status Code:", resp.status_code)
        print("Content Type:", resp.headers.get("content-type"))
        print("Response Snippet:", resp.text[:200])
                
asyncio.run(test_search())
