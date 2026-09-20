"""Swiggy Instamart platform client — Playwright WAF bypass + httpx search.

Architecture:
  1. WAF session: A module-level SwiggyWAFSession singleton launches Playwright once,
     loads https://www.swiggy.com/instamart with the correct userLocation cookie,
     and captures aws-waf-token + deviceId. These are reused for all subsequent httpx
     requests without re-launching a browser.

  2. resolve_store(lat, lng): Fetches /stores/instamart/item/{placeholder} with
     Googlebot UA + userLocation cookie → extracts storeId from Redux state.
     Enables hex-grid store discovery without WAF session.

  3. search(query, store_id, lat, lng): POST to /api/instamart/search/v2 with WAF
     cookies + x-device-id header. Returns list[ProductResult].

  4. product_at_store(product_id, store_id, lat, lng): Fetches the item detail page
     and extracts pricing, stock, and external_product_id from Redux state.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import urllib.parse
from typing import Any

import httpx

from .base import PlatformClient, PlatformError, ProductResult, StoreResolution
from ..normalization import parse_quantity

log = logging.getLogger("swiggy")

WEB_BASE = "https://www.swiggy.com"
STORES_BASE = f"{WEB_BASE}/stores/instamart/item"
CDN_BASE = "https://instamart-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto"

_PROBE_PRODUCT_ID = "F9UK3KLPCI"
_UA_BOT = "Googlebot/2.1 (+http://www.google.com/bot.html)"
_UA_BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0"


class SwiggyError(PlatformError):
    pass


# ─── Module-level WAF session singleton ────────────────────────────────────────

class _WAFSession:
    """Holds a cached WAF cookie dict and device ID, shared across all SwiggyClient instances."""

    def __init__(self):
        self._cookies: dict[str, str] | None = None
        self._device_id: str = ""
        self._init_lock: asyncio.Lock | None = None
        self._initialized = False

    def _get_lock(self) -> asyncio.Lock:
        # Lazily create lock in the running event loop
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
        return self._init_lock

    @property
    def cookies(self) -> dict[str, str]:
        return self._cookies or {}

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def ready(self) -> bool:
        return self._initialized and bool(self._cookies)

    async def ensure(self, lat: float, lng: float) -> None:
        if self._initialized:
            return
        lock = self._get_lock()
        async with lock:
            if self._initialized:
                return
            await self._initialize(lat, lng)

    async def _initialize(self, lat: float, lng: float) -> None:
        log.info("WAFSession: launching Playwright to capture WAF cookies lat=%s lng=%s", lat, lng)
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log.error("playwright not installed — run: uv add playwright && playwright install chromium")
            self._initialized = True
            return

        loc_val = urllib.parse.quote(json.dumps({"lat": lat, "lng": lng, "address": "India"}))

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
                )
                context = await browser.new_context(
                    user_agent=_UA_BROWSER,
                    viewport={"width": 1440, "height": 900},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )
                await context.add_cookies([{
                    "name": "userLocation",
                    "value": loc_val,
                    "domain": ".swiggy.com",
                    "path": "/",
                }])
                page = await context.new_page()
                try:
                    await page.goto("https://www.swiggy.com/instamart", wait_until="domcontentloaded", timeout=60000)
                    for _ in range(30):
                        cookies = await context.cookies()
                        names = {c["name"] for c in cookies}
                        if "aws-waf-token" in names and "deviceId" in names:
                            log.info("WAFSession: WAF token acquired")
                            break
                        await asyncio.sleep(1)
                    else:
                        log.warning("WAFSession: aws-waf-token/deviceId not found after 30s")

                    all_cookies = await context.cookies()
                    self._cookies = {c["name"]: c["value"] for c in all_cookies}
                    raw_did = urllib.parse.unquote(self._cookies.get("deviceId", ""))
                    self._device_id = raw_did.removeprefix("s:").split(".")[0]
                    log.info("WAFSession: ready. device_id=%r keys=%s", self._device_id, list(self._cookies.keys()))
                finally:
                    await browser.close()
        except Exception as e:
            log.error("WAFSession: Playwright initialization failed: %s", e, exc_info=True)

        self._initialized = True

    def invalidate(self) -> None:
        self._cookies = None
        self._device_id = ""
        self._initialized = False
        self._init_lock = None


_waf_session = _WAFSession()


# ─── Page fetcher (Googlebot bypass for item pages) ────────────────────────────

def _make_location_cookie(lat: float, lng: float) -> str:
    val = json.dumps({"lat": lat, "lng": lng, "address": "India"})
    return "userLocation=" + urllib.parse.quote(val)


async def _fetch_page(product_id: str, lat: float | None = None, lng: float | None = None) -> str:
    url = f"{STORES_BASE}/{product_id}"
    headers: dict[str, str] = {
        "User-Agent": _UA_BOT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
    }
    if lat is not None and lng is not None:
        headers["Cookie"] = _make_location_cookie(lat, lng)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0), follow_redirects=True, http2=False) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.text
            log.warning("Swiggy /stores/ returned %s for %s", resp.status_code, product_id)
            return ""
    except Exception as e:
        log.error("Swiggy fetch error for %s: %s", product_id, e)
        return ""


# ─── Redux state extractor ─────────────────────────────────────────────────────

def _extract_redux(html: str, product_id: str = "") -> dict:
    result: dict[str, Any] = {
        "store_id": None, "serviceable": False, "eta_minutes": None,
        "name": None, "brand": None, "in_stock": None, "is_avail": None,
        "price": None, "mrp": None, "image_url": None, "raw_quantity": None,
        "external_product_id": None,
    }

    if not html:
        return result

    sid_m = re.search(r'"storeDetailsV2"\s*:\s*\{"storeId"\s*:\s*"(\d+)"', html)
    if sid_m:
        result["store_id"] = sid_m.group(1)
    result["serviceable"] = bool(result.get("store_id"))

    eta_m = re.search(r'"sla"\s*:\s*\{"value"\s*:\s*"(\d+)"', html)
    if eta_m:
        try:
            val = int(eta_m.group(1))
            if val > 0:
                result["eta_minutes"] = val
        except ValueError:
            pass

    prod_idx = html.find('"productV2"')
    if prod_idx >= 0:
        chunk = html[prod_idx: prod_idx + 20000]

        name_m = re.search(r'"displayName"\s*:\s*"([^"]+)"', chunk)
        brand_m = re.search(r'"brand"\s*:\s*"([^"]+)"', chunk)
        instock_m = re.search(r'"inStock"\s*:\s*(true|false)', chunk)
        isavail_m = re.search(r'"isAvail"\s*:\s*(true|false)', chunk)

        result["name"] = name_m.group(1) if name_m else None
        result["brand"] = brand_m.group(1) if brand_m else None
        result["in_stock"] = (instock_m.group(1) == "true") if instock_m else None
        result["is_avail"] = (isavail_m.group(1) == "true") if isavail_m else None

        var_blocks = re.split(r'(?=\{"skuId"\s*:)', chunk)
        matched_block: str | None = None
        listing_block: str | None = None
        first_block: str | None = None

        for blk in var_blocks:
            if not blk.startswith('{"skuId"'):
                continue
            if first_block is None:
                first_block = blk
            sku_m = re.search(r'"skuId"\s*:\s*"([^"]+)"', blk)
            spin_m = re.search(r'"spinId"\s*:\s*"([^"]+)"', blk)
            is_listing = '"listingVariant":true' in blk.replace(" ", "")
            if product_id:
                if sku_m and sku_m.group(1) == product_id:
                    matched_block = blk
                    break
                if spin_m and spin_m.group(1) == product_id:
                    matched_block = blk
                    break
            if is_listing and not listing_block:
                listing_block = blk

        target_block = matched_block or listing_block or first_block

        if target_block:
            sku_in_block = re.search(r'"skuId"\s*:\s*"([^"]+)"', target_block)
            if sku_in_block:
                result["external_product_id"] = sku_in_block.group(1)
            qty_m = re.search(r'"quantityDescription"\s*:\s*"([^"]+)"', target_block)
            offer_m = re.search(r'"offerPrice"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"(\d+)"', target_block)
            mrp_m = re.search(r'"mrp"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"(\d+)"', target_block)
            if qty_m:
                result["raw_quantity"] = qty_m.group(1)
            if offer_m:
                result["price"] = float(offer_m.group(1))
            if mrp_m:
                result["mrp"] = float(mrp_m.group(1))
        else:
            pack_m = re.search(r'"quantityDescription"\s*:\s*"([^"]+)"', chunk)
            if pack_m:
                result["raw_quantity"] = pack_m.group(1)
            offer_m = re.search(r'"offerPrice"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"(\d+)"', chunk)
            mrp_m = re.search(r'"mrp"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"(\d+)"', chunk)
            if offer_m:
                result["price"] = float(offer_m.group(1))
            if mrp_m:
                result["mrp"] = float(mrp_m.group(1))

        img_m = re.search(r'"imageIds"\s*:\s*\["([^"]+)"', chunk)
        if img_m:
            result["image_url"] = f"{CDN_BASE}/{img_m.group(1)}"

    if not result["image_url"]:
        jsonld_blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        for raw in jsonld_blocks:
            try:
                data = json.loads(raw.strip())
                if isinstance(data, list):
                    data = next((x for x in data if isinstance(x, dict) and x.get("@type") == "Product"), {})
                if isinstance(data, dict) and data.get("@type") == "Product":
                    images = data.get("image", [])
                    if isinstance(images, str):
                        result["image_url"] = images
                    elif isinstance(images, list) and images:
                        result["image_url"] = images[0]
                    elif isinstance(images, dict):
                        result["image_url"] = images.get("url") or images.get("contentUrl")
                    if result["image_url"]:
                        break
            except Exception:
                pass

    return result


def _data_to_product(data: dict, product_id: str) -> ProductResult:
    if not data.get("name"):
        return ProductResult(status="not_carried", external_product_id=product_id or None)

    in_stock = data.get("in_stock")
    status = "in_stock" if in_stock is True else "out_of_stock"
    price = data.get("price")
    qty_str = data.get("raw_quantity") or ""
    title_str = data.get("name") or ""
    variant_label = qty_str if qty_str else title_str
    nq = parse_quantity(variant_label)
    ext_id = data.get("external_product_id") or product_id or None

    return ProductResult(
        status=status,
        name=data.get("name"),
        brand=data.get("brand"),
        image_url=data.get("image_url"),
        price=price,
        mrp=data.get("mrp"),
        pack_count=nq.pack_count if nq else None,
        quantity_per_pack=nq.quantity_per_pack if nq else None,
        quantity_unit=nq.quantity_unit if nq else None,
        total_quantity=nq.total_quantity if nq else None,
        total_quantity_unit=nq.total_quantity_unit if nq else None,
        price_per_unit=(price / nq.total_quantity) if (price and nq and nq.total_quantity and nq.total_quantity > 0) else None,
        raw_variant=variant_label,
        quantity_confidence=nq.confidence if nq else None,
        external_product_id=ext_id,
    )


def _parse_search_response(data: dict) -> list[ProductResult]:
    """Parse /api/instamart/search/v2 JSON into ProductResult objects."""
    results = []
    cards = (data.get("data") or {}).get("cards") or []

    for card in cards:
        inner = (card.get("card") or {}).get("card") or {}
        grid = (inner.get("gridElements") or {}).get("infoWithStyle") or {}
        items = grid.get("items") or []

        for item in items:
            item_in_stock = item.get("inStock", True)
            item_name = item.get("displayName") or ""
            variations = item.get("variations") or []

            if not variations:
                log.debug("Item '%s' has no variations — skipping", item_name)
                continue

            for v in variations:
                sku = v.get("skuId") or ""
                name = v.get("displayName") or item_name
                brand = v.get("brandName") or item.get("brand") or ""
                image_ids = v.get("imageIds") or []
                image_url = f"{CDN_BASE}/{image_ids[0]}" if image_ids else None

                price_block = v.get("price") or {}

                def _money(val: dict | None) -> float:
                    if not val:
                        return 0.0
                    return float(val.get("units") or 0) + float(val.get("nanos") or 0) / 1_000_000_000

                mrp = _money(price_block.get("mrp"))
                offer = _money(price_block.get("offerPrice"))

                if mrp <= 0 or offer <= 0:
                    log.debug("Skipping '%s' (sku=%s): mrp=%s offer=%s", name, sku, mrp, offer)
                    continue

                qty_str = v.get("quantityDescription") or ""
                nq = parse_quantity(qty_str or name)

                results.append(ProductResult(
                    status="in_stock" if item_in_stock else "out_of_stock",
                    name=name,
                    brand=brand,
                    image_url=image_url,
                    price=offer,
                    mrp=mrp,
                    raw_variant=qty_str or name,
                    quantity_confidence=nq.confidence if nq else None,
                    pack_count=nq.pack_count if nq else None,
                    quantity_per_pack=nq.quantity_per_pack if nq else None,
                    quantity_unit=nq.quantity_unit if nq else None,
                    total_quantity=nq.total_quantity if nq else None,
                    total_quantity_unit=nq.total_quantity_unit if nq else None,
                    price_per_unit=(offer / nq.total_quantity) if (nq and nq.total_quantity and nq.total_quantity > 0) else None,
                    external_product_id=sku,
                ))

    log.info("_parse_search_response: %d products from %d cards", len(results), len(cards))
    return results


# ─── SwiggyClient ──────────────────────────────────────────────────────────────

class SwiggyClient(PlatformClient):
    """Swiggy Instamart client using WAF-bypassed httpx + module-level WAF singleton."""

    def __init__(self, proxy_url: str | None = None, concurrency: int = 6, transport=None):
        self._semaphore = asyncio.Semaphore(concurrency)
        self._product_cache: dict[tuple[str, str], ProductResult] = {}
        self._product_cache_lock = asyncio.Lock()

    @property
    def platform_name(self) -> str:
        return "swiggy"

    @property
    def display_name(self) -> str:
        return "Swiggy Instamart"

    @property
    def supports_sweep(self) -> bool:
        return True

    @property
    def supports_geocoding(self) -> bool:
        return False

    async def aclose(self) -> None:
        pass

    async def resolve_share_link(self, url: str) -> str | None:
        from ..links import SWIGGY_PRODUCT_RE, INSTAMART_SHORT_RE
        m = SWIGGY_PRODUCT_RE.search(url) or INSTAMART_SHORT_RE.search(url)
        return m.group(1) if m else None

    async def resolve_store(self, lat: float, lng: float, product_id: str | None = None) -> StoreResolution:
        """Probe coordinate to discover serving Instamart dark store via Googlebot UA trick."""
        pid = product_id or _PROBE_PRODUCT_ID
        async with self._semaphore:
            html = await _fetch_page(pid, lat, lng)

        data = _extract_redux(html, pid)
        store_id = data.get("store_id")
        eta = data.get("eta_minutes")

        if not store_id:
            grid_lat = round(lat / 0.04) * 0.04
            grid_lng = round(lng / 0.04) * 0.04
            store_id = f"synthetic_{grid_lat:.2f}_{grid_lng:.2f}"
            log.debug("resolve_store: no store at (%.4f, %.4f) → synthetic %s", lat, lng, store_id)

        return StoreResolution(
            serviceable=True,
            store_id=store_id,
            store_name=f"Instamart ({eta} min)" if eta else "Instamart",
            eta_minutes=eta,
            city=None,
        )

    async def search(self, query: str, store_id: str, lat: float, lng: float) -> list[ProductResult]:
        """Keyword search via /api/instamart/search/v2 using WAF session cookies."""
        await _waf_session.ensure(lat, lng)

        if not _waf_session.ready:
            log.error("search: WAF session not ready for query '%s'", query)
            return []

        sid = store_id if not store_id.startswith("synthetic_") else ""
        url = (
            "https://www.swiggy.com/api/instamart/search/v2"
            f"?offset=0&ageConsent=false&voiceSearchTrackingId="
            f"&storeId={sid}&primaryStoreId={sid}&secondaryStoreId="
        )
        headers = {
            "User-Agent": _UA_BROWSER,
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
            "query": query,
            "search_results_offset": "0",
            "page_type": "INSTAMART_SEARCH_PAGE",
            "is_pre_search_tag": False,
        }

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0),
                    follow_redirects=True,
                    cookies=_waf_session.cookies,
                ) as client:
                    resp = await client.post(url, headers=headers, json=body)

                if resp.status_code in (403, 202):
                    log.warning("search: WAF blocked (%s) for '%s' — invalidating session and retrying", resp.status_code, query)
                    _waf_session.invalidate()
                    await _waf_session.ensure(lat, lng)
                    if _waf_session.device_id:
                        headers["x-device-id"] = _waf_session.device_id
                    continue

                if resp.status_code != 200:
                    log.error("search: status %s for '%s'. Body: %s", resp.status_code, query, resp.text[:500])
                    return []

                if not resp.text.strip():
                    log.error("search: empty response for '%s'", query)
                    return []

                data = resp.json()
                results = _parse_search_response(data)
                log.info("search: query='%s' store='%s' → %d results", query, store_id, len(results))
                return results

            except Exception as e:
                log.error("search: exception for '%s': %s", query, e, exc_info=True)
                return []
                
        return []

    async def product_at_store(
        self,
        product_id: str,
        store_id: str,
        lat: float | None = None,
        lng: float | None = None,
    ) -> ProductResult:
        """Check stock of specific product at specific store via item page scrape."""
        cache_key = (product_id, store_id)
        async with self._product_cache_lock:
            if cache_key in self._product_cache:
                return self._product_cache[cache_key]

        async with self._semaphore:
            html = await _fetch_page(product_id, lat, lng)

        data = _extract_redux(html, product_id)
        result = _data_to_product(data, product_id)

        async with self._product_cache_lock:
            self._product_cache[cache_key] = result

        return result

    async def product_at_location(self, product_id: str, lat: float, lng: float) -> ProductResult:
        async with self._semaphore:
            html = await _fetch_page(product_id, lat, lng)
        data = _extract_redux(html, product_id)
        return _data_to_product(data, product_id)
