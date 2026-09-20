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
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, params=params, json=json_data)
        print(resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            print("Keys:", data.keys())
            if "data" in data:
                print("Data keys:", data["data"].keys())
                widgets = data["data"].get("widgets", [])
                print("Widgets:", len(widgets))
                
asyncio.run(test_search())
