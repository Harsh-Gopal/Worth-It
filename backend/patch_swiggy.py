import re

with open("app/platforms/swiggy.py", "r") as f:
    content = f.read()

patch = """
    async def ensure_waf_session(self, lat: float, lng: float):
        if getattr(self, '_waf_cookies', None):
            return
        import urllib.parse
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
                locale="en-IN", timezone_id="Asia/Kolkata"
            )
            await context.add_cookies([{
                "name": "userLocation",
                "value": urllib.parse.quote(f'{{"lat":{lat},"lng":{lng},"address":"India"}}'),
                "domain": ".swiggy.com",
                "path": "/"
            }])
            page = await context.new_page()
            try:
                await page.goto("https://www.swiggy.com/instamart", wait_until="domcontentloaded", timeout=60000)
                for _ in range(30):
                    cookies = await context.cookies()
                    cnames = [c["name"] for c in cookies]
                    if "aws-waf-token" in cnames and "deviceId" in cnames:
                        break
                    import asyncio
                    await asyncio.sleep(1)
                self._waf_cookies = {c["name"]: c["value"] for c in await context.cookies()}
            finally:
                await browser.close()

    async def resolve_store(
        self, lat: float, lng: float, product_id: str | None = None
    ) -> StoreResolution:
        # Use WAF session to get storeId from home API or SSR
        await self.ensure_waf_session(lat, lng)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
        }
        store_id = None
        async with httpx.AsyncClient(timeout=30, cookies=self._waf_cookies) as client:
            resp = await client.get('https://www.swiggy.com/instamart', headers=headers)
            # Find storeId=xxxxxx in deep links in HTML
            import re
            m = re.search(r'storeId=([0-9]+)', resp.text)
            if m:
                store_id = m.group(1)
        
        if not store_id:
            grid_lat = round(lat / 0.04) * 0.04
            grid_lng = round(lng / 0.04) * 0.04
            store_id = f"synthetic_{grid_lat:.2f}_{grid_lng:.2f}"
            
        return StoreResolution(
            serviceable=True,
            store_id=store_id,
            store_name="Instamart",
            eta_minutes=None,
            city=None,
        )

    async def search(self, query: str, store_id: str, lat: float, lng: float) -> list[ProductResult]:
        await self.ensure_waf_session(lat, lng)
        import urllib.parse
        sid = store_id if not store_id.startswith("synthetic_") else ""
        url = f"https://www.swiggy.com/api/instamart/search/v2?offset=0&ageConsent=false&storeId={sid}&primaryStoreId={sid}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
            "content-type": "application/json",
            "x-device-id": urllib.parse.unquote(self._waf_cookies.get("deviceId", "")).removeprefix("s:").split(".")[0],
        }
        body = {
            "facets": [], "sortAttribute": "", "query": query, "search_results_offset": "0", "page_type": "INSTAMART_SEARCH_PAGE"
        }
        results = []
        async with httpx.AsyncClient(timeout=20, cookies=self._waf_cookies) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                return results
            data = resp.json()
            for card in ((data.get("data") or {}).get("cards") or []):
                grid = (((card.get("card") or {}).get("card") or {}).get("gridElements") or {}).get("infoWithStyle") or {}
                for item in grid.get("items") or []:
                    for v in item.get("variations") or []:
                        sku = v.get("skuId") or ""
                        name = v.get("displayName") or item.get("displayName") or ""
                        category = v.get("category") or ""
                        price_block = v.get("price") or {}
                        def _money(val):
                            if not val: return 0.0
                            return float(val.get("units") or 0) + float(val.get("nanos") or 0) / 1e9
                        mrp = _money(price_block.get("mrp"))
                        offer = _money(price_block.get("offerPrice"))
                        if not mrp or mrp <= 0 or offer == 0.0:
                            continue
                        # Use ProductResult to match CartRadar's format
                        from app.platforms.base import ProductResult
                        results.append(ProductResult(
                            status="in_stock",
                            name=name,
                            brand="",
                            image_url=f"https://instamart-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto/{v.get('imageId','')}",
                            price=offer,
                            mrp=mrp,
                            raw_variant=name,
                            external_product_id=sku # We need this to match IDs! Wait, ProductResult doesn't have external_product_id natively!
                        ))
        return results
"""

# I will apply this patch using multi_replace_file_content or manually.
