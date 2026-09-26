"""Zepto platform client.

Architecture (production-safe):
  1. search(): Navigate to search page with Playwright, intercept the BFF JSON response.
     - Much more reliable than DOM scraping or raw HTTPX (avoids 429/WAF).
     - Parses the BFF JSON directly for accurate price/MRP/stock data.
     - Uses the browser's native headers (including compatible_components), so WAF accepts it.
  2. resolve_store(): Navigate to homepage, read serviceability cookie.
  3. product_at_store(): Navigate to product page, intercept product-detail BFF response.

Key API findings (2026-09-26):
  - Search endpoint: POST https://bff-gateway.zepto.com/user-search-service/api/v3/search
  - Triggered automatically during /search?query=... page navigation
  - All prices are in PAISE (divide by 100 to get INR)
  - pagination: nextPageParams.pageNumber, hasReachedEnd
  - Product URL: https://www.zeptonow.com/pn/{slug}/pvid/{pvid}
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from urllib.parse import quote, unquote

from ..base import PlatformClient, PlatformError, ProductResult, StoreResolution
from ...normalization import parse_quantity

log = logging.getLogger("zepto")

# --- Constants ---

WEB_BASE = "https://www.zepto.com"
BFF_BASE = "https://bff-gateway.zepto.com"
CDN_BASE = "https://cdn.zeptonow.com/production"

SEARCH_BFF_URL = f"{BFF_BASE}/user-search-service/api/v3/search"
PRODUCT_DETAIL_BFF_URL = f"{BFF_BASE}/product-assortment-service/api/v2/product-detail"

APP_VERSION = "17.0.1"
SAMPLE_STORE_ID = "0059ff6a-7eb0-477a-a7f5-69256f2c444b"

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0"

_NAV_TIMEOUT_MS = 25000  # ms for page navigation
_API_WAIT_S = 6.0        # seconds to wait for BFF response after navigation

_BROWSER = None
_PLAYWRIGHT = None
_LOCK = asyncio.Lock()

async def _get_firefox_browser():
    """Lazy-start a shared Playwright Firefox browser instance."""
    global _BROWSER, _PLAYWRIGHT
    async with _LOCK:
        if _BROWSER is None:
            try:
                from playwright.async_api import async_playwright
                _PLAYWRIGHT = await async_playwright().start()
                _BROWSER = await _PLAYWRIGHT.firefox.launch(headless=True)
                log.info("Zepto: Playwright Firefox started successfully")
            except Exception as exc:
                log.error("Zepto: Playwright Firefox FAILED to start: %s", exc)
                _PLAYWRIGHT = None
                _BROWSER = None
                raise ZeptoError(f"Playwright Firefox launch failed: {exc}") from exc
    return _BROWSER

async def _close_firefox_browser():
    global _BROWSER, _PLAYWRIGHT
    async with _LOCK:
        if _BROWSER:
            await _BROWSER.close()
            _BROWSER = None
        if _PLAYWRIGHT:
            await _PLAYWRIGHT.stop()
            _PLAYWRIGHT = None


# --- Error Types ---

class ZeptoError(PlatformError):
    pass

class ZeptoWafBlockedError(ZeptoError):
    pass

class ZeptoNetworkError(ZeptoError):
    pass


# --- Category mapping ---

WORTH_IT_TO_ZEPTO_QUERY: dict[str, str] = {
    "Sports & Fitness": "sports fitness protein",
    "Protein": "protein",
    "Beverages": "beverages drinks",
    "Snacks": "snacks",
    "Dairy": "dairy",
    "Fruits & Vegetables": "fruits vegetables",
    "Grocery": "grocery",
    "Baby Care": "baby care",
    "Personal Care": "personal care",
    "Cleaning": "cleaning household",
    "Health & Medicine": "health medicine",
    "Pet Care": "pet care",
}


def _category_to_query(category: str) -> str:
    """Convert a Worth-It category to a Zepto search query."""
    if category in WORTH_IT_TO_ZEPTO_QUERY:
        return WORTH_IT_TO_ZEPTO_QUERY[category]
    return category.lower()


# --- Product parsing ---

def _parse_product_result(product_response: dict) -> ProductResult | None:
    """Parse a productResponse object from Zepto BFF search API into a ProductResult.

    Key fields:
      product.name, product.brand, product.id
      productVariant.id: PVID (used in product URL)
      productVariant.mrp: MRP in PAISE
      productVariant.images: [{"path": "..."}]
      productVariant.formattedPacksize: "1 pc (200 ml)"
      discountedSellingPrice: selling price in PAISE
      mrp: MRP in PAISE (top-level preferred)
      outOfStock: boolean
      availableQuantity: int
    """
    if not product_response:
        return None

    product_meta = product_response.get("product") or {}
    product_variant = product_response.get("productVariant") or {}

    name = product_meta.get("name")
    if not name:
        return None

    brand = product_meta.get("brand") or ""

    # Image URL
    images = product_variant.get("images") or product_meta.get("images") or []
    image_url = None
    if images:
        first_image = images[0]
        if isinstance(first_image, dict):
            path = first_image.get("path", "")
            image_url = f"{CDN_BASE}/{path}" if path else None

    # Prices in PAISE -> divide by 100 for INR
    mrp_paise = (
        product_response.get("mrp")
        or product_variant.get("mrp")
        or product_meta.get("mrp")
    )
    price_paise = (
        product_response.get("discountedSellingPrice")
        or product_response.get("sellingPrice")
        or mrp_paise
    )

    mrp = mrp_paise / 100.0 if mrp_paise else None
    price = price_paise / 100.0 if price_paise else None

    # Stock detection
    out_of_stock = bool(product_response.get("outOfStock"))
    available_qty = product_response.get("availableQuantity")
    if available_qty is not None and int(available_qty) <= 0:
        out_of_stock = True

    status = "out_of_stock" if out_of_stock else "in_stock"

    # Quantity parsing
    pack_size_str = product_variant.get("formattedPacksize") or ""
    nq = parse_quantity(pack_size_str) if pack_size_str else None

    # Build product URL
    pvid = product_variant.get("id") or ""
    product_name_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    product_url = f"{WEB_BASE}/pn/{product_name_slug}/pvid/{pvid}" if pvid else WEB_BASE

    return ProductResult(
        status=status,
        name=name,
        brand=brand,
        image_url=image_url,
        price=price,
        mrp=mrp,
        available_quantity=available_qty,
        pack_count=nq.pack_count if nq else None,
        quantity_per_pack=nq.quantity_per_pack if nq else None,
        quantity_unit=nq.quantity_unit if nq else None,
        total_quantity=nq.total_quantity if nq else None,
        total_quantity_unit=nq.total_quantity_unit if nq else None,
        price_per_unit=(price / nq.total_quantity) if (price and nq and nq.total_quantity and nq.total_quantity > 0) else None,
        raw_variant=pack_size_str or None,
        quantity_confidence=nq.confidence if nq else None,
        external_product_id=pvid or product_response.get("objectId") or "",
    )


def _parse_search_response(data: dict) -> list[ProductResult]:
    """Parse Zepto BFF search API response into a list of ProductResult.

    Response layout:
      layout[].widgetName = "SEARCHED_PRODUCTS_N"
      layout[].data.resolver.type = "product_grid"
      layout[].data.resolver.data.items[].productResponse = { ... }
    """
    results = []
    seen_pvids: set[str] = set()
    layout = data.get("layout") or []

    for widget in layout:
        widget_name = widget.get("widgetName", "")
        if "SEARCHED_PRODUCTS" not in widget_name:
            continue

        widget_data = widget.get("data") or {}
        resolver = widget_data.get("resolver") or {}
        resolver_data = resolver.get("data") or {}
        items = resolver_data.get("items") or []

        for item in items:
            product_response = item.get("productResponse")
            if not product_response:
                continue

            pv = product_response.get("productVariant") or {}
            pvid = pv.get("id") or product_response.get("objectId") or ""
            if pvid and pvid in seen_pvids:
                continue
            if pvid:
                seen_pvids.add(pvid)

            result = _parse_product_result(product_response)
            if result and result.name:
                results.append(result)

    return results


def _parse_product_detail(data: dict, requested_pvid: str) -> ProductResult:
    """Parse Zepto BFF product-detail API response."""
    if (data.get("fallbackType") or "NONE") != "NONE":
        return ProductResult(status="not_carried", name=(data.get("product") or {}).get("name"))
    product = data.get("product") or {}
    store_products = product.get("storeProducts") or []
    if not store_products:
        return ProductResult(status="not_carried", name=product.get("name"))

    target_sp = None
    for sp in store_products:
        variant = sp.get("productVariant") or {}
        if variant.get("id") == requested_pvid:
            target_sp = sp
            break

    not_found_in_store = target_sp is None
    if not_found_in_store:
        target_sp = store_products[0]

    sp = target_sp
    variant = sp.get("productVariant") or {}
    images = variant.get("images") or product.get("images") or []
    image_url = f"{CDN_BASE}/{images[0]['path']}" if images else None

    price_paise = sp.get("discountedSellingPrice") or sp.get("sellingPrice") or sp.get("superSaverSellingPrice")
    mrp_paise = sp.get("mrp") or variant.get("mrp")
    price = price_paise / 100 if price_paise else None
    mrp = mrp_paise / 100 if mrp_paise else None

    if not_found_in_store:
        status = "not_carried"
    elif sp.get("outOfStock"):
        status = "out_of_stock"
    else:
        status = "in_stock"

    variant_label = variant.get("name") or variant.get("displayName") or ""
    nq = parse_quantity(variant_label) if variant_label else None

    return ProductResult(
        status=status,
        name=product.get("name"),
        brand=product.get("brand"),
        image_url=image_url,
        price=price,
        mrp=mrp,
        available_quantity=sp.get("availableQuantity"),
        pack_count=nq.pack_count if nq else None,
        quantity_per_pack=nq.quantity_per_pack if nq else None,
        quantity_unit=nq.quantity_unit if nq else None,
        total_quantity=nq.total_quantity if nq else None,
        total_quantity_unit=nq.total_quantity_unit if nq else None,
        price_per_unit=(price / nq.total_quantity) if (price and nq and nq.total_quantity and nq.total_quantity > 0) else None,
        raw_variant=variant_label or None,
        quantity_confidence=nq.confidence if nq else None,
    )


# --- Core browser helpers ---

async def _get_playwright():
    """Import and return playwright async_api module."""
    try:
        from playwright.async_api import async_playwright
        return async_playwright
    except ImportError:
        raise ZeptoError("playwright not installed -- run: uv add playwright && playwright install firefox")


async def _navigate_and_set_location(context, lat: float, lng: float) -> None:
    """Set location cookie and navigate to homepage to establish Zepto session."""
    position = quote(json.dumps({"latitude": lat, "longitude": lng}, separators=(",", ":")), safe="")
    for domain in [".zeptonow.com", ".zepto.com"]:
        await context.add_cookies([{
            "name": "user_position",
            "value": position,
            "domain": domain,
            "path": "/"
        }])


async def _probe_location_for_store(lat: float, lng: float) -> dict:
    """Use Playwright Firefox to probe a location and get store ID from serviceability cookie."""
    try:
        browser = await _get_firefox_browser()
        try:
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            await _navigate_and_set_location(context, lat, lng)

            page = await context.new_page()
            try:
                await page.goto(f"{WEB_BASE}/", wait_until="commit", timeout=_NAV_TIMEOUT_MS)
            except Exception as e:
                if "NS_BINDING_ABORTED" not in str(e):
                    log.debug("Zepto probe navigation (partial, OK): %s", e)
            await asyncio.sleep(2)

            cookies = await context.cookies()
            cookie_names = [c["name"] for c in cookies]
            log.info("Zepto probe cookies found: %s", cookie_names)
            
            serviceability_cookie = next((c for c in cookies if c["name"] == "serviceability"), None)
            if not serviceability_cookie:
                log.warning("Zepto: serviceability cookie missing!")
                return {"serviceable": False}

            data = json.loads(unquote(serviceability_cookie["value"]))
            primary = data.get("primaryStore") or {}
            secondary = data.get("secondaryStore") or {}
            info = data.get("storeDetailedInfo") or {}

            if not (primary.get("serviceable") and primary.get("storeId")):
                return {"serviceable": False}

            all_stores = []
            stores_data = data.get("storesData", {})
            if stores_data:
                for s_id, s_info in stores_data.items():
                    if s_info.get("serviceable"):
                        all_stores.append(s_id)
            else:
                all_stores.append(primary["storeId"])
                if secondary.get("serviceable") and secondary.get("storeId"):
                    all_stores.append(secondary["storeId"])

            return {
                "serviceable": True,
                "store_id": primary["storeId"],
                "store_name": info.get("name"),
                "city": info.get("city"),
                "eta_minutes": primary.get("etaInMinutes"),
                "all_store_ids": list(set(all_stores))
            }
        finally:
            await context.close()
    except Exception as e:
        log.warning("Zepto location probe failed: %s", e)
        return {"serviceable": False}


async def _search_via_browser(query: str, lat: float, lng: float, max_products: int = 60) -> list[ProductResult]:
    """Navigate to Zepto search page and intercept the BFF JSON response."""
    all_results: list[ProductResult] = []
    seen_pvids: set[str] = set()
    bff_responses: list[dict] = []
    response_event = asyncio.Event()

    try:
        browser = await _get_firefox_browser()
        try:
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            await _navigate_and_set_location(context, lat, lng)

            page = await context.new_page()

            async def on_response(response):
                url = response.url
                if SEARCH_BFF_URL in url and "filters" not in url:
                    try:
                        data = await response.json()
                        bff_responses.append(data)
                        if data.get("totalProductCount", 0) > 0:
                            response_event.set()
                            log.info("[ZEPTO] search: captured BFF response, total=%s", data.get("totalProductCount"))
                    except Exception as e:
                        log.debug("[ZEPTO] search: BFF response parse error: %s", e)

            page.on("response", on_response)

            search_url = f"{WEB_BASE}/search?query={quote(query)}"
            log.info("[ZEPTO] search: navigating to %s", search_url)
            try:
                await page.goto(search_url, wait_until="commit", timeout=_NAV_TIMEOUT_MS)
            except Exception as e:
                if "NS_BINDING_ABORTED" not in str(e) and "net::ERR" not in str(e):
                    log.warning("[ZEPTO] search: navigation error (may be OK): %s", e)

            try:
                await asyncio.wait_for(response_event.wait(), timeout=_API_WAIT_S)
            except asyncio.TimeoutError:
                log.warning("[ZEPTO] search: timed out waiting for BFF response after %.0fs", _API_WAIT_S)

            if not bff_responses:
                await asyncio.sleep(3.0)
        finally:
            await context.close()
    except Exception as e:
        log.error("[ZEPTO] search: browser error: %s", e, exc_info=True)
        return []

    # Parse all captured BFF responses
    raw_count = 0
    for data in bff_responses:
        page_results = _parse_search_response(data)
        raw_count += len(page_results)
        for pr in page_results:
            pvid = pr.external_product_id or ""
            if pvid in seen_pvids:
                continue
            if pvid:
                seen_pvids.add(pvid)
            if pr.price is None or pr.status == "out_of_stock":
                continue
            all_results.append(pr)
            if len(all_results) >= max_products:
                break

    log.info(
        "[ZEPTO] search complete: query=%r raw=%d final=%d",
        query, raw_count, len(all_results)
    )
    return all_results[:max_products]


# --- ZeptoClient ---

class ZeptoClient(PlatformClient):
    """Zepto platform client.

    search() navigates to the Zepto search page via Playwright Firefox and
    intercepts the BFF JSON response for accurate product data.
    This avoids WAF 429 issues while remaining completely DOM-scraping-free.
    """

    def __init__(self, *args, **kwargs):
        self._search_sem = asyncio.Semaphore(2)  # Max 2 concurrent browser searches

    @property
    def platform_name(self) -> str:
        return "zepto"

    @property
    def display_name(self) -> str:
        return "Zepto"

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
        """Resolve the serving store for a location."""
        res = await _probe_location_for_store(lat, lng)
        return StoreResolution(
            serviceable=res.get("serviceable", False),
            store_id=res.get("store_id") if res.get("serviceable") else None,
            store_name=res.get("store_name"),
            city=res.get("city"),
            eta_minutes=res.get("eta_minutes"),
        )

    async def product_at_store(
        self,
        product_id: str,
        store_id: str,
        lat: float | None = None,
        lng: float | None = None,
    ) -> ProductResult:
        """Check availability of a specific product (pvid) at a store."""
        product_result = None
        detail_event = asyncio.Event()

        try:
            browser = await _get_firefox_browser()
            try:
                context = await browser.new_context(viewport={"width": 1280, "height": 800})
                if lat and lng:
                    await _navigate_and_set_location(context, lat, lng)

                page = await context.new_page()

                async def on_response(response):
                    url = response.url
                    if PRODUCT_DETAIL_BFF_URL in url and product_id in url:
                        try:
                            data = await response.json()
                            nonlocal product_result
                            product_result = _parse_product_detail(data, product_id)
                            detail_event.set()
                        except Exception as e:
                            log.debug("[ZEPTO] product_at_store: parse error: %s", e)

                page.on("response", on_response)

                product_url = f"{WEB_BASE}/pvid/{product_id}"
                try:
                    await page.goto(product_url, wait_until="commit", timeout=_NAV_TIMEOUT_MS)
                except Exception as e:
                    if "NS_BINDING_ABORTED" not in str(e):
                        log.debug("[ZEPTO] product_at_store: navigation partial: %s", e)

                try:
                    await asyncio.wait_for(detail_event.wait(), timeout=8.0)
                except asyncio.TimeoutError:
                    pass

            finally:
                await context.close()
        except Exception as e:
            log.warning("[ZEPTO] product_at_store: error for pvid=%s: %s", product_id, e)
            return ProductResult(status="error")

        return product_result or ProductResult(status="not_carried")

    async def search(
        self,
        query: str,
        store_id: str,
        lat: float,
        lng: float,
        max_products: int = 60,
        is_category: bool = False,
    ) -> list[ProductResult]:
        """Search Zepto for products matching a query.

        Navigates to the Zepto search URL and intercepts the BFF API response.
        This is the only reliable approach that bypasses WAF/rate-limiting.

        Args:
            query: keyword or category name to search
            store_id: Zepto store UUID (used for context, actual location is from lat/lng)
            lat, lng: user location coordinates
            max_products: cap on returned products
            is_category: if True, maps category name to optimized query
        """
        search_query = _category_to_query(query) if is_category else query

        log.info(
            "[ZEPTO] search: query=%r lat=%.4f lng=%.4f max=%d",
            search_query, lat, lng, max_products
        )

        async with self._search_sem:
            return await _search_via_browser(search_query, lat, lng, max_products)

    async def product_at_location(self, product_id: str, lat: float, lng: float) -> ProductResult:
        res = await self.resolve_store(lat, lng, product_id=product_id)
        if not res.serviceable or not res.store_id:
            return ProductResult(status="not_carried")
        return await self.product_at_store(product_id, res.store_id, lat=lat, lng=lng)


# --- Deprecated: ZeptoPlaywrightSession (kept for backward compatibility) ---

class ZeptoPlaywrightSession:
    """Legacy Playwright session -- kept for backward compatibility only.

    The new production path uses browser-interception in ZeptoClient.search().
    """

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self._p = None
        self._waf_cookies = {}

    async def __aenter__(self):
        from playwright.async_api import async_playwright
        self._p = await async_playwright().start()
        self.browser = await self._p.firefox.launch(headless=True)
        self.context = await self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = await self.context.new_page()
        try:
            await self.page.goto(f"{WEB_BASE}/", wait_until="commit", timeout=15000)
        except Exception as e:
            if "NS_BINDING_ABORTED" not in str(e):
                log.debug("ZeptoPlaywrightSession: navigation partial: %s", e)
        await asyncio.sleep(2)
        cookies = await self.context.cookies()
        self._waf_cookies = {c["name"]: c["value"] for c in cookies}
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.browser:
            await self.browser.close()
        if self._p:
            await self._p.stop()

    async def probe_location(self, lat: float, lng: float) -> dict:
        """Probe a location and return store resolution."""
        cookies = await self.context.cookies()
        keep_cookies = [c for c in cookies if c["name"] not in ["serviceability", "storeId", "user_position", "selectedAddress", "addressId"]]
        await self.context.clear_cookies()
        if keep_cookies:
            await self.context.add_cookies(keep_cookies)

        position = quote(json.dumps({"latitude": lat, "longitude": lng}, separators=(",", ":")), safe="")
        for domain in [".zepto.com", ".zeptonow.com"]:
            await self.context.add_cookies([{
                "name": "user_position",
                "value": position,
                "domain": domain,
                "path": "/"
            }])

        try:
            try:
                await self.page.goto(f"{WEB_BASE}/", wait_until="commit", timeout=15000)
            except Exception as e:
                if "NS_BINDING_ABORTED" not in str(e):
                    raise
            await asyncio.sleep(2)

            cookies = await self.context.cookies()
            serviceability_cookie = next((c for c in cookies if c["name"] == "serviceability"), None)
            if not serviceability_cookie:
                raise ZeptoWafBlockedError("Zepto did not set a serviceability cookie.")

            data = json.loads(unquote(serviceability_cookie["value"]))
            primary = data.get("primaryStore") or {}
            secondary = data.get("secondaryStore") or {}
            info = data.get("storeDetailedInfo") or {}

            if not (primary.get("serviceable") and primary.get("storeId")):
                return {"serviceable": False}

            all_stores = []
            stores_data = data.get("storesData", {})
            if stores_data:
                for s_id, s_info in stores_data.items():
                    if s_info.get("serviceable"):
                        all_stores.append(s_id)
            else:
                all_stores.append(primary["storeId"])
                if secondary.get("serviceable") and secondary.get("storeId"):
                    all_stores.append(secondary["storeId"])

            return {
                "serviceable": True,
                "store_id": primary["storeId"],
                "store_name": info.get("name"),
                "city": info.get("city"),
                "eta_minutes": primary.get("etaInMinutes"),
                "all_store_ids": list(set(all_stores))
            }
        except Exception as e:
            if "TimeoutError" in str(type(e)) or "Target closed" in str(e):
                raise ZeptoWafBlockedError("Playwright timed out during probe") from e
            raise ZeptoError(f"Probe failed: {e}") from e

    async def check_product(self, store_id: str, pvid: str) -> ProductResult:
        """Check product availability using the Playwright session."""
        product_result = None
        detail_event = asyncio.Event()

        async def on_response(response):
            url = response.url
            if PRODUCT_DETAIL_BFF_URL in url and pvid in url:
                try:
                    data = await response.json()
                    nonlocal product_result
                    product_result = _parse_product_detail(data, pvid)
                    detail_event.set()
                except:
                    pass

        self.page.on("response", on_response)

        product_page_url = f"{WEB_BASE}/pvid/{pvid}"
        try:
            await self.page.goto(product_page_url, wait_until="commit", timeout=_NAV_TIMEOUT_MS)
        except Exception as e:
            if "NS_BINDING_ABORTED" not in str(e):
                log.debug("check_product: navigation partial: %s", e)

        try:
            await asyncio.wait_for(detail_event.wait(), timeout=8.0)
        except asyncio.TimeoutError:
            pass

        self.page.remove_listener("response", on_response)
        return product_result or ProductResult(status="not_carried")
