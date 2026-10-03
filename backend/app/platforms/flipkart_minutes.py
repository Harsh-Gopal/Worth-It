"""Flipkart Minutes platform client.

Flipkart Minutes:
  Requires location. Uses GPS injection via Playwright browser geolocation:

  1. Set browser geolocation to the user's lat/lng coordinates.
  2. Navigate to the HYPERLOCAL product URL.
  3. If Flipkart shows the address selection bottom sheet, click "Use my current location".
  4. Wait for the browser URL to change away from the hyperlocal-preview-page using
     wait_for_url() with a proper timeout — NOT a fixed sleep.
  5. If the URL is now the product page, wait for content to render, then extract price
     from both application/ld+json AND DOM scraping fallback.
  6. If the URL is still the preview page, try typing a Nominatim-resolved pincode into
     the search box (same approach as BigBasket: lat/lng → Nominatim → pincode → input).
"""

from __future__ import annotations

import asyncio
import logging

from app.geo.geocoding import nom_reverse_geocode
from .base import PlatformClient, ProductResult, StoreResolution, PlatformProduct
from app.core.browser import BrowserManager

log = logging.getLogger("flipkart_minutes")

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Extracts product data from ld+json
_LD_JSON_JS = '''() => {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
        try {
            const data = JSON.parse(script.textContent);
            let items = Array.isArray(data) ? data : [data];
            for (const item of items) {
                if (item["@type"] === "Product" && item.offers && item.offers.price) {
                    return {
                        price: parseFloat(item.offers.price),
                        name: item.name || null,
                        brand: (item.brand && item.brand.name) || null,
                        image: (typeof item.image === "string") ? item.image
                               : (Array.isArray(item.image) ? item.image[0] : null),
                    };
                }
            }
        } catch (e) {}
    }
    return null;
}'''

_DOM_PRICE_JS = r'''() => {
    function extractPrice(sel) {
        // Walk text nodes inside matching elements to find the ₹ price
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
        let node;
        while ((node = walker.nextNode())) {
            const t = node.textContent.trim();
            if (/^₹\d/.test(t)) {
                // Check if this text node's ancestor matches our selector
                let el = node.parentElement;
                for (let i = 0; i < 4; i++) {
                    if (!el) break;
                    if (el.matches(sel)) {
                        const num = parseFloat(t.replace(/[^\d.]/g, ""));
                        if (!isNaN(num) && num > 0 && num < 500000) return num;
                    }
                    el = el.parentElement;
                }
            }
        }
        return null;
    }

    // selling price first (v1zwn22), then MRP (v1zwn20)
    const selling = extractPrice("div.v1zwn22");
    if (selling) return selling;
    const mrp = extractPrice("div.v1zwn20");
    if (mrp) return mrp;

    // Standard Flipkart (non-Minutes) fallback
    for (const sel of ["div.Nx9bqj", "div[class*='_30jeq3']"]) {
        const el = document.querySelector(sel);
        if (el) {
            const num = parseFloat(el.textContent.replace(/[^\d.]/g, ""));
            if (!isNaN(num) && num > 0) return num;
        }
    }
    return null;
}'''

_UNSERVICEABLE_SLUGS = ("flipkart-minutes-store", "hyperlocal-preview-page")

def _is_unserviceable(url: str) -> bool:
    return any(slug in url for slug in _UNSERVICEABLE_SLUGS)

async def _extract_product_result(page) -> ProductResult:
    """Extract price from ld+json, then fallback to DOM scraping.
    
    Flipkart Minutes product pages have NO ld+json — price is React-rendered.
    We wait 5s for the DOM to fully render before scraping.
    """
    await page.wait_for_timeout(5000)

    result = await page.evaluate(_LD_JSON_JS)
    if result and result.get("price"):
        log.info("Flipkart Minutes: price extracted from ld+json: %s", result["price"])
        return ProductResult(
            status="in_stock",
            price=result["price"],
            mrp=result["price"],
            name=result.get("name"),
            brand=result.get("brand"),
            image_url=result.get("image"),
        )

    dom_price = await page.evaluate(_DOM_PRICE_JS)
    if dom_price:
        log.info("Flipkart Minutes: price=%s (DOM)", dom_price)
        return ProductResult(
            status="in_stock", 
            price=dom_price, 
            mrp=dom_price,
            name=None,
            image_url=None
        )

    log.warning("Flipkart Minutes: on product page but price not found — returning out_of_stock")
    return ProductResult(status="out_of_stock")

class FlipkartMinutesClient(PlatformClient):
    """Flipkart Minutes (HYPERLOCAL) platform client."""

    def __init__(self):
        super().__init__()
        self._result_cache: dict[str, ProductResult] = {}
        self._sem = asyncio.Semaphore(2)

    @property
    def platform_name(self) -> str:
        return "minutes"

    @property
    def display_name(self) -> str:
        return "Flipkart Minutes"

    @property
    def supports_sweep(self) -> bool:
        return True

    @property
    def supports_geocoding(self) -> bool:
        return False

    async def aclose(self) -> None:
        pass

    async def resolve_store(
        self, lat: float, lng: float, product_id: str | None = None
    ) -> StoreResolution:
        store_id = f"fm_coverage_{round(lat, 3)}_{round(lng, 3)}"

        if f"{product_id}_{store_id}" in self._result_cache:
            return StoreResolution(
                serviceable=True,
                store_id=store_id,
                store_name="Flipkart Minutes Coverage Area",
                eta_minutes=None,
                city=None,
            )

        test_url = f"https://www.flipkart.com/product/p/itme?pid={product_id}&marketplace=HYPERLOCAL" if product_id else "https://www.flipkart.com/?marketplace=HYPERLOCAL"

        async with self._sem:
            ctx_opts = {
                "user_agent": _UA,
                "geolocation": {"longitude": lng, "latitude": lat},
                "permissions": ["geolocation"]
            }
            try:
                async with BrowserManager.get_page(ctx_opts) as page:
                    await page.goto(test_url, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(4000)

                    if not _is_unserviceable(page.url):
                        log.info("Flipkart Minutes: landed directly on serviceable page: %s", page.url)
                        if product_id:
                            result = await _extract_product_result(page)
                            self._result_cache[f"{product_id}_{store_id}"] = result
                        return StoreResolution(
                            serviceable=True, store_id=store_id, store_name="Flipkart Minutes Coverage Area", city=None
                        )

                    loc_btns = await page.locator("text=/Use my current location/i").all()
                    if loc_btns:
                        log.info("Flipkart Minutes: clicking 'Use my current location'")
                        await loc_btns[0].click(timeout=5000)

                        try:
                            await page.wait_for_url(
                                lambda url: not _is_unserviceable(url),
                                timeout=12000,
                            )
                            log.info("Flipkart Minutes: URL changed to serviceable page — SERVICEABLE")
                            if product_id:
                                result = await _extract_product_result(page)
                                self._result_cache[f"{product_id}_{store_id}"] = result
                            return StoreResolution(
                                serviceable=True, store_id=store_id, store_name="Flipkart Minutes Coverage Area", city=None
                            )
                        except Exception:
                            log.info("Flipkart Minutes: GPS location not accepted — still on preview page")

                    pincode = await nom_reverse_geocode(lat, lng)
                    log.info("Flipkart Minutes: trying pincode fallback, pincode=%s", pincode)

                    if pincode:
                        inp_sel = "input[placeholder*='Search'], input[placeholder*='area'], input[placeholder*='pin code'], input[placeholder*='pincode']"
                        inputs = await page.locator(inp_sel).all()

                        for inp in inputs:
                            try:
                                await inp.click()
                                await inp.fill(pincode)
                                await page.wait_for_timeout(2000)

                                suggestions = await page.locator(
                                    "li[role='option'], [class*='Suggestion'], [class*='suggestion'], [class*='listItem']"
                                ).all()
                            
                                if suggestions:
                                    await suggestions[0].click(timeout=5000)
                                else:
                                    await inp.press("Enter")

                                try:
                                    await page.wait_for_url(
                                        lambda url: not _is_unserviceable(url),
                                        timeout=10000,
                                    )
                                    log.info("Flipkart Minutes: pincode strategy navigated to serviceable page")
                                    if product_id:
                                        result = await _extract_product_result(page)
                                        self._result_cache[f"{product_id}_{store_id}"] = result
                                    return StoreResolution(
                                        serviceable=True, store_id=store_id, store_name="Flipkart Minutes Coverage Area", city=None
                                    )
                                except Exception:
                                    log.info("Flipkart Minutes: pincode strategy also unserviceable")
                                break
                            except Exception as e:
                                log.debug("Flipkart Minutes: pincode input error: %s", e)

                    return StoreResolution(serviceable=False)

            except Exception as e:
                log.warning("Flipkart Minutes extraction failed: %s", e)
                from .base import PlatformError
                raise PlatformError(f"Flipkart Minutes error: {e}")

    async def product_at_store(
        self,
        product_id: str,
        store_id: str,
        lat: float | None = None,
        lng: float | None = None,
    ) -> ProductResult:
        orig_key = f"{product_id}_fm_coverage_{round(lat or 0, 3)}_{round(lng or 0, 3)}"
        if orig_key in self._result_cache:
            return self._result_cache.pop(orig_key)
        
        if lat is not None and lng is not None:
            res = await self.resolve_store(lat, lng, product_id)
            if res.serviceable:
                orig_key = f"{product_id}_fm_coverage_{round(lat, 3)}_{round(lng, 3)}"
                return self._result_cache.pop(orig_key, ProductResult(status="error"))
            
        return ProductResult(status="not_carried")

    async def product_at_location(self, product_id: str, lat: float, lng: float) -> ProductResult:
        store = await self.resolve_store(lat, lng, product_id=product_id)
        if not store.serviceable or not store.store_id:
            return ProductResult(status="not_carried")
        return await self.product_at_store(product_id, store.store_id, lat=lat, lng=lng)

    async def search(self, query: str, store_id: str, lat: float, lng: float, max_products: int = 60, is_category: bool = False) -> list[PlatformProduct]:
        search_url = f"https://www.flipkart.com/search?q={query}&marketplace=HYPERLOCAL"
        
        products = []
        captured_responses = []

        async def handle_response(response):
            if "api/4/page/fetch" in response.url:
                try:
                    data = await response.json()
                    captured_responses.append(data)
                except Exception:
                    pass

        async with self._sem:
            ctx_opts = {
                "user_agent": _UA,
                "geolocation": {"longitude": lng, "latitude": lat},
                "permissions": ["geolocation"]
            }
            try:
                async with BrowserManager.get_page(ctx_opts) as page:
                    page.on("response", handle_response)
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(4000)
                    
                    if not _is_unserviceable(page.url):
                        pass
                    else:
                        loc_btns = await page.locator("text=/Use my current location/i").all()
                        if loc_btns:
                            await loc_btns[0].click(timeout=5000)
                            try:
                                await page.wait_for_url(
                                    lambda u: not _is_unserviceable(u),
                                    timeout=12000,
                                )
                                await page.wait_for_timeout(3000)
                            except Exception:
                                log.info("Flipkart Minutes search: location not accepted")
                                return []

                    for data in captured_responses:
                        slots = data.get("RESPONSE", {}).get("slots", [])
                        for slot in slots:
                            widget = slot.get("widget", {})
                            if widget.get("type") == "PRODUCT_SUMMARY_EXTENDED":
                                for prod in widget.get("data", {}).get("products", []):
                                    val = prod.get("productInfo", {}).get("value", {})
                                    name = val.get("titles", {}).get("title")
                                    if not name:
                                        continue
                                    
                                    brand = val.get("titles", {}).get("superTitle")
                                    pid = val.get("id")
                                    
                                    pricing = val.get("pricing", {})
                                    final_price = pricing.get("finalPrice", {}).get("value")
                                    
                                    prices = pricing.get("prices", [])
                                    mrp = final_price
                                    for p in prices:
                                        if p.get("priceType") == "MRP" or p.get("name") == "Maximum Retail Price":
                                            mrp = p.get("value")
                                    
                                    in_stock = val.get("inventory", {}).get("inStock", True)
                                    image_url = None
                                    try:
                                        image_url = val.get("media", {}).get("images", [])[0].get("url")
                                    except IndexError:
                                        pass
                                    
                                    products.append(PlatformProduct(
                                        external_product_id=pid,
                                        name=name,
                                        url=f"https://www.flipkart.com/product/p/itme?pid={pid}&marketplace=HYPERLOCAL",
                                        image_url=image_url,
                                        price=final_price,
                                        mrp=mrp,
                                        stock=in_stock,
                                        category=query
                                    ))
            except Exception as e:
                log.warning("Flipkart Minutes search failed: %s", e)

        unique_products = {p.external_product_id: p for p in products}
        return list(unique_products.values())
