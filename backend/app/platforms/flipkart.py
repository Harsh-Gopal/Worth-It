"""Flipkart platform client.

Normal Flipkart:
  Uses Playwright to fetch the product page and extracts price from application/ld+json.
  No location is required for standard Flipkart availability.
"""

from __future__ import annotations

import asyncio
import logging
import re

import httpx

from .base import PlatformClient, ProductResult, StoreResolution, PlatformProduct
from app.core.browser import BrowserManager

log = logging.getLogger("flipkart")

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



class FlipkartClient(PlatformClient):
    """Standard Flipkart platform client (non-Minutes)."""

    @property
    def platform_name(self) -> str:
        return "flipkart"

    @property
    def display_name(self) -> str:
        return "Flipkart"

    @property
    def supports_sweep(self) -> bool:
        return False

    @property
    def supports_geocoding(self) -> bool:
        return False

    async def aclose(self) -> None:
        pass


    async def product_at_location(self, product_id: str, lat: float, lng: float) -> ProductResult:
        """Fetch price from normal Flipkart. Location not required for stock status."""
        url = f"https://www.flipkart.com/product/p/itme?pid={product_id}&marketplace=FLIPKART"
        try:
            async with BrowserManager.get_page({"user_agent": _UA}) as page:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)
                result = await page.evaluate(_LD_JSON_JS)
                if result and result.get("price"):
                    return ProductResult(
                        status="in_stock",
                        price=result["price"],
                        mrp=result["price"],
                        name=result.get("name"),
                        brand=result.get("brand"),
                        image_url=result.get("image"),
                    )
                return ProductResult(status="not_carried")
        except Exception as e:
            log.warning("Flipkart normal extraction failed: %s", e)
            return ProductResult(status="error")

    async def resolve_store(self, lat: float, lng: float, product_id: str | None = None) -> StoreResolution:
        return StoreResolution(serviceable=True, store_id="default")

    async def product_at_store(self, product_id: str, store_id: str, lat: float | None = None, lng: float | None = None) -> ProductResult:
        return await self.product_at_location(product_id, lat or 0.0, lng or 0.0)



