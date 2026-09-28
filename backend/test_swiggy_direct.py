from curl_cffi import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
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

print("POST v3...")
r = requests.post(
    "https://www.swiggy.com/api/instamart/search/v3?offset=0&ageConsent=false&voiceSearchTrackingId=&storeId=1403831&primaryStoreId=1403831&secondaryStoreId=",
    json=body,
    headers=headers,
    impersonate="chrome120"
)
print("Status:", r.status_code)
print("Text length:", len(r.text))
print("Text snippet:", r.text[:200])
