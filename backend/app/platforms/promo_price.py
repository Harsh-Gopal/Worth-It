"""
Instamart Flash / Promotional Price Extractor
=============================================

Instamart sometimes shows a special "flash sale" price highlighted in blue,
separate from the normal offer price. This is visible as:

    ₹26  Only till 10 PM

The data lives in `flashSalePriceDetails` inside the Redux initial state
(`window.___INITIAL_STATE___.productV2.itemData.variations[N].price`).

This module is **completely standalone** — it does NOT touch or modify the
existing SwiggyClient / product_at_store flow. Normal price tracking cannot
regress because of this module.

API contract:
  fetch_flash_price(product_id, lat, lng) -> FlashPriceResult

FlashPriceResult fields:
  product_id        str   – The Instamart product ID passed in
  name              str | None
  brand             str | None
  image_url         str | None
  normal_price      float | None  – Regular offer price (offerPrice)
  mrp               float | None
  special_price     float | None  – Flash sale price (None if no flash sale)
  non_flash_price   float | None  – The price after the flash sale ends
  flash_end_time    str | None    – Human-readable end time, e.g. "10 PM"
  redemption_limit  int | None    – Max units per user at flash price
  extraction_method str           – How the price was found ('redux_state' / 'none')
  serviceable       bool          – Whether the location is served by Instamart
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any

import httpx

log = logging.getLogger("promo_price")

# Reuse the same CDN base as swiggy.py
_CDN_BASE = "https://instamart-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto"
_STORES_BASE = "https://www.swiggy.com/stores/instamart/item"
_UA_BOT = "Googlebot/2.1 (+http://www.google.com/bot.html)"


# ─── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class FlashPriceResult:
    product_id: str
    name: str | None = None
    brand: str | None = None
    image_url: str | None = None
    # Normal pricing
    normal_price: float | None = None
    mrp: float | None = None
    # Flash / promotional pricing
    special_price: float | None = None
    non_flash_price: float | None = None
    flash_end_time: str | None = None
    redemption_limit: int | None = None
    # Metadata
    extraction_method: str = "none"
    serviceable: bool = False
    error: str | None = None

    @property
    def has_flash_sale(self) -> bool:
        return self.special_price is not None


# ─── HTTP helper ─────────────────────────────────────────────────────────────

def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(20.0),
        follow_redirects=True,
        http2=False,
    )


def _make_location_cookie(lat: float, lng: float) -> str:
    val = json.dumps({"lat": lat, "lng": lng, "address": "India"})
    return "userLocation=" + urllib.parse.quote(val)


async def _fetch_item_page(product_id: str, lat: float, lng: float) -> str:
    """Fetch the Instamart item detail page using Googlebot UA to bypass WAF."""
    url = f"{_STORES_BASE}/{product_id}"
    headers: dict[str, str] = {
        "User-Agent": _UA_BOT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
        "Cookie": _make_location_cookie(lat, lng),
    }
    try:
        async with _get_client() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                log.info("promo_price: fetched item page for %s (lat=%.4f, lng=%.4f) — %d bytes",
                         product_id, lat, lng, len(resp.text))
                return resp.text
            log.warning("promo_price: item page status %s for product_id=%s", resp.status_code, product_id)
            return ""
    except Exception as e:
        log.error("promo_price: HTTP error for %s: %s", product_id, e)
        return ""


# ─── Parser ───────────────────────────────────────────────────────────────────

def _parse_item_page(html: str, product_id: str) -> FlashPriceResult:
    """
    Extract flash price data from the HTML of an Instamart item detail page.

    Strategy:
      1. Locate the `productV2` block inside the serialised Redux state.
      2. Within that block find the `variations` array and pick the matching
         SKU (or listing variant, or first variant as fallback).
      3. Extract `flashSalePriceDetails` — the blue-highlighted promotional price.
      4. Also extract normal `offerPrice` and `mrp` for comparison.
    """
    result = FlashPriceResult(product_id=product_id)

    if not html:
        result.error = "empty_response"
        return result

    # ── 1. Locate productV2 chunk ───────────────────────────────────────────
    prod_idx = html.find('"productV2"')
    if prod_idx < 0:
        log.warning("promo_price: 'productV2' not found in HTML for %s", product_id)
        result.error = "product_not_found"
        return result

    chunk = html[prod_idx: prod_idx + 40000]

    # Serviceability: presence of storeId in the page means this location is served
    store_m = re.search(r'"storeId"\s*:\s*"(\d+)"', html[:prod_idx + 5000])
    result.serviceable = bool(store_m)

    # ── 2. Basic product metadata ───────────────────────────────────────────
    name_m = re.search(r'"displayName"\s*:\s*"([^"]+)"', chunk)
    brand_m = re.search(r'"brand"\s*:\s*"([^"]+)"', chunk)
    result.name = name_m.group(1) if name_m else None
    result.brand = brand_m.group(1) if brand_m else None

    img_m = re.search(r'"imageIds"\s*:\s*\["([^"]+)"', chunk)
    if not img_m:
        img_m = re.search(r'"imageId"\s*:\s*"([^"]+)"', chunk)
    if img_m:
        result.image_url = f"{_CDN_BASE}/{img_m.group(1)}"

    # ── 3. Find the correct variation block ─────────────────────────────────
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

    if not target_block:
        log.warning("promo_price: no variation block found for %s", product_id)
        result.error = "no_variation_block"
        return result

    # ── 4. Extract normal price ─────────────────────────────────────────────
    offer_m = re.search(
        r'"offerPrice"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"(\d+)"',
        target_block
    )
    mrp_m = re.search(
        r'"mrp"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"(\d+)"',
        target_block
    )
    if offer_m:
        result.normal_price = float(offer_m.group(1))
    if mrp_m:
        result.mrp = float(mrp_m.group(1))

    # ── 5. Extract flashSalePriceDetails ────────────────────────────────────
    flash_idx = target_block.find('"flashSalePriceDetails"')
    if flash_idx >= 0:
        flash_chunk = target_block[flash_idx: flash_idx + 2000]

        # flashSalePrice
        fsp_m = re.search(
            r'"flashSalePrice"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"?(\d+)"?',
            flash_chunk
        )
        # nonFlashSalePrice
        nfsp_m = re.search(
            r'"nonFlashSalePrice"\s*:\s*\{"currencyCode"\s*:\s*"INR"\s*,\s*"units"\s*:\s*"?(\d+)"?',
            flash_chunk
        )
        # flashSaleEndTime e.g. "10 PM"
        end_time_m = re.search(r'"flashSaleEndTime"\s*:\s*"([^"]+)"', flash_chunk)
        # redemptionUnits (per-user limit)
        redemption_m = re.search(r'"redemptionUnits"\s*:\s*(\d+)', flash_chunk)

        if fsp_m:
            result.special_price = float(fsp_m.group(1))
            result.extraction_method = "redux_state"
            log.info(
                "promo_price: flash sale detected for %s — special_price=%.0f, normal_price=%s, end_time=%s",
                product_id, result.special_price, result.normal_price,
                end_time_m.group(1) if end_time_m else "N/A",
            )
        else:
            log.info("promo_price: 'flashSalePriceDetails' key present but no flashSalePrice for %s", product_id)

        if nfsp_m:
            result.non_flash_price = float(nfsp_m.group(1))
        if end_time_m:
            result.flash_end_time = end_time_m.group(1)
        if redemption_m:
            result.redemption_limit = int(redemption_m.group(1))
    else:
        # No flash sale for this product
        if result.normal_price is not None:
            result.extraction_method = "redux_state"
        log.info("promo_price: no flash sale for %s (normal price=%.0f)",
                 product_id, result.normal_price or 0)

    return result


# ─── Public API ───────────────────────────────────────────────────────────────

async def fetch_flash_price(product_id: str, lat: float, lng: float) -> FlashPriceResult:
    """
    Fetch promotional / flash sale price for an Instamart product.

    This is a standalone function. It does NOT interact with SwiggyClient,
    alert rules, or any other tracking mechanism.

    Args:
        product_id: The Instamart product ID (skuId / spinId), e.g. "917UXELNGA"
        lat: User latitude (determines which dark store serves the location)
        lng: User longitude

    Returns:
        FlashPriceResult with special_price=None if no flash sale is running.
    """
    html = await _fetch_item_page(product_id, lat, lng)
    return _parse_item_page(html, product_id)
