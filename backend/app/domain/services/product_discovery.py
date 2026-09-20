import asyncio
from typing import List, Any
import httpx
from app.domain.models.product import CanonicalProduct, InstamartProduct
import logging

log = logging.getLogger("product_discovery")
from app.domain.services.product_matcher import ProductMatcher
from app.platforms.swiggy import SwiggyClient

FETCH_JS = """
async (payload) => {
    try {
        const response = await fetch(payload.url, {
            method: payload.method,
            headers: payload.headers,
            body: payload.body,
        });
        const text = await response.text();
        return {
            status: response.status,
            headers: Object.fromEntries(response.headers.entries()),
            text: text
        };
    } catch (e) {
        return {error: e.toString()};
    }
}
"""

class ProductDiscoveryEngine:
    """
    Takes a broad keyword and discovers exact product variations by searching locally.
    """
    def __init__(self, client: httpx.Client, store_id: str, lat: float = None, lng: float = None):
        self.client = client
        self.store_id = store_id
        self.lat = lat
        self.lng = lng

    async def _fetch_search_playwright(self, query: str) -> dict:
        """
        Bypass WAF using Playwright to get cookies, then use httpx to fetch the data.
        """
        log.info(f"Using Playwright WAF bypass for search: {query}")
        
        final_cookies = {}
        USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1440, "height": 900},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata"
                )
                
                # Setup userLocation to ensure we get correct store prices
                import urllib.parse
                await context.add_cookies([
                    {
                        "name": "userLocation",
                        "value": urllib.parse.quote(f'{{"lat":{self.lat or 25.6075768},"lng":{self.lng or 85.083029},"address":"India"}}'),
                        "domain": ".swiggy.com",
                        "path": "/"
                    }
                ])
                
                page = await context.new_page()
                try:
                    await page.goto("https://www.swiggy.com/instamart", wait_until="domcontentloaded", timeout=60000)
                    
                    # Wait for the challenge to clear and cookies to be set
                    for _ in range(30):
                        cookies = await context.cookies()
                        cnames = [c["name"] for c in cookies]
                        if "aws-waf-token" in cnames and "deviceId" in cnames:
                            break
                        await asyncio.sleep(1)
                    else:
                        log.warning("WAF token or deviceId not found after 30s")
                        
                    final_cookies = {c["name"]: c["value"] for c in await context.cookies()}
                finally:
                    await browser.close()
                    
            if not final_cookies:
                return {}
                
            sid = self.store_id if not self.store_id.startswith("synthetic_") else ""
            url = f"https://www.swiggy.com/api/instamart/search/v2?offset=0&ageConsent=false&voiceSearchTrackingId=&storeId={sid}&primaryStoreId={sid}&secondaryStoreId="
            
            headers = {
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "Accept-Language": "en-IN",
                "content-type": "application/json",
                "x-build-version": "2.367.0",
                "Origin": "https://www.swiggy.com",
                "Referer": "https://www.swiggy.com/instamart",
            }
            if "deviceId" in final_cookies:
                headers["x-device-id"] = urllib.parse.unquote(final_cookies["deviceId"]).removeprefix("s:").split(".")[0]
            
            body = {
                "facets": [],
                "sortAttribute": "",
                "query": query,
                "search_results_offset": "0",
                "page_type": "INSTAMART_SEARCH_PAGE",
                "is_pre_search_tag": False,
            }
            
            # Create a separate client to ensure pristine headers
            import httpx
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, cookies=final_cookies) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    if not resp.text.strip():
                        log.error("Empty response text from WAF/CloudFront!")
                        return {}
                    return resp.json()
                else:
                    log.error(f"Playwright HTTPX fetch failed with status {resp.status_code}")
                    return {}
                    
        except Exception as e:
            log.error(f"Playwright search failed: {e}")
            return {}

    def _parse_products(self, payload: dict) -> List[InstamartProduct]:
        products = []
        for card in ((payload.get("data") or {}).get("cards") or []):
            inner = (card.get("card") or {}).get("card") or {}
            grid = (inner.get("gridElements") or {}).get("infoWithStyle") or {}
            for item in grid.get("items") or []:
                for v in item.get("variations") or []:
                    sku = v.get("skuId") or ""
                    name = v.get("displayName") or item.get("displayName") or ""
                    category = v.get("category") or ""
                    
                    price_block = v.get("price") or {}
                    
                    def _money(val):
                        if not val:
                            return 0.0
                        return float(val.get("units") or 0) + float(val.get("nanos") or 0) / 1e9
                    
                    mrp = _money(price_block.get("mrp"))
                    offer = _money(price_block.get("offerPrice"))
                    
                    if not mrp or mrp <= 0 or offer == 0.0:
                        continue
                        
                    products.append(InstamartProduct(
                        external_product_id=sku,
                        name=name,
                        url=f"https://www.swiggy.com/instamart/item/{sku}",
                        price=offer,
                        mrp=mrp,
                        stock=True, # Simplify stock for discovery phase
                        category=category
                    ))
        return products

    async def discover(self, keyword: str, match_keywords: List[str] = None, exclude_keywords: List[str] = None) -> List[CanonicalProduct]:
        """
        Search the local store for the keyword, then run it through the matcher.
        Returns a list of CanonicalProducts representing exact variations.
        """
        matcher = ProductMatcher(keyword, match_keywords, exclude_keywords)
        
        log.info(f"Using SwiggyClient to search for '{keyword}' at store {self.store_id}")
        
        async with httpx.AsyncClient(timeout=15.0) as async_client:
            swiggy = SwiggyClient(async_client)
            raw_products = await swiggy.search(keyword, self.store_id, self.lat or 12.9716, self.lng or 77.5946)
        
        canonical_products = []
        seen_ids = set()
        
        for p in raw_products:
            if matcher.matches(p):
                canonical = matcher.create_canonical(p)
                if canonical.id not in seen_ids:
                    canonical_products.append(canonical)
                    seen_ids.add(canonical.id)
                    
        return canonical_products
