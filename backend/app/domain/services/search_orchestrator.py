"""
Search orchestrator: the core geographic deal-hunting engine.

Flow:
  keyword / URLs → local store check → progressive radius expansion → store
  discovery (hex-grid probing) → targeted product checks → deal evaluation →
  SSE events streamed to the frontend.

SSE event schema (all events carry `search_id` and `data`):

  search_started         → { keyword, search_mode }
  local_search_started   → { store_id }
  product_discovered     → { count, candidates: [name, ...] }
  deal_found             → { <DealEvent dict> }
  product_check_failed   → { store_id, product_id, error }
  local_search_completed → { deals_found }
  radius_expansion_started → { radii: [km, ...] }
  radius_scan_started    → { radius_km }
  probe_started          → { count }
  store_discovered       → { store_id, lat, lng, name }
  probe_completed        → {}
  store_scan_started     → { stores_count }
  product_check_started  → { store_id, count }
  product_check_completed → { store_id }
  store_scan_failed      → { store_id, error }
  radius_completed       → { radius_km, deals_found }
  search_completed       → { message, total_deals }
  search_cancelled       → { message }
  search_error           → { message }

deal_found data shape (maps directly to frontend DealResult):
  {
    "product": {
      "external_product_id": str,
      "name": str,
      "price": float,
      "mrp": float,
      "stock": bool,
      "image_url": str | null,
      "product_url": str
    },
    "store": {
      "id": str,
      "name": str | null,
      "lat": float | null,
      "lng": float | null,
      "distance_km": float
    },
    "discount_percent": float,
    "price_drop_percent": float | null,
    "historical_low_before_now": float | null,
    "is_historical_low": bool,
    "trigger_reasons": [str, ...]
  }
"""
import logging
import asyncio
import re
from typing import AsyncIterator, List, Dict, Set, Optional

import httpx

from app.domain.models.deal import DealCondition
from app.domain.models.product import CanonicalProduct, InstamartProduct
from app.domain.models.store import Store
from app.domain.services.product_discovery import ProductDiscoveryEngine
from app.domain.services.deal_engine import DealEngine
from app.domain.services.deal_ranker import DealRanker
from app.geo.store_cache import StoreCache
from app.geo.hex_grid import HexGridGenerator
from app.geo.store_discovery import StoreDiscoveryService
from app.platforms.instamart.client import search, product_at_store
from app.domain.services.price_history_service import PriceHistoryService

log = logging.getLogger("orchestrator")

# Regex for extracting product ID from Instamart URLs
_ITEM_ID_RE = re.compile(r"/instamart/item/(\d+)", re.IGNORECASE)
_ITEM_PARAM_RE = re.compile(r"[?&]itemId=(\d+)", re.IGNORECASE)


def _extract_product_id(url: str) -> Optional[str]:
    m = _ITEM_ID_RE.search(url) or _ITEM_PARAM_RE.search(url)
    return m.group(1) if m else None


def _build_deal_event(
    product: InstamartProduct,
    store_id: str,
    store: Optional[Store],
    eval_result,
) -> Dict:
    """Build the canonical deal_found data payload."""
    dist = store.distance_km if store and store.distance_km is not None else 0.0
    return {
        "product": {
            "external_product_id": product.external_product_id,
            "name": product.name,
            "price": product.price,
            "mrp": product.mrp,
            "stock": product.stock,
            "image_url": product.image_url,
            "product_url": product.url or f"https://www.swiggy.com/instamart/item/{product.external_product_id}",
        },
        "store": {
            "id": store_id,
            "name": store.name if store else None,
            "lat": store.lat if store else None,
            "lng": store.lng if store else None,
            "distance_km": dist,
        },
        "discount_percent": eval_result.discount_percent,
        "price_drop_percent": eval_result.price_drop_percent,
        "historical_low_before_now": eval_result.historical_low,
        "is_historical_low": eval_result.is_historical_low,
        "trigger_reasons": eval_result.trigger_reasons,
        # Legacy flat fields for alert_engine compatibility
        "_flat": {
            "canonical_id": product.canonical_product_id or f"canonical_{product.external_product_id}",
            "instamart_product_id": product.external_product_id,
            "product_name": product.name,
            "price": product.price,
            "mrp": product.mrp,
            "discount_pct": eval_result.discount_percent,
            "previous_price": eval_result.previous_price,
            "price_drop_percent": eval_result.price_drop_percent,
            "triggers": eval_result.trigger_reasons,
            "store_id": store_id,
            "distance_km": dist,
        }
    }


class DealSearchOrchestrator:
    MAX_SEARCH_RADIUS_KM = 20.0

    def __init__(
        self,
        client: httpx.Client,
        store_cache: StoreCache,
        center_lat: float,
        center_lng: float,
        local_store_id: str,
        price_history_service: Optional[PriceHistoryService] = None,
    ):
        self.client = client
        self.store_cache = store_cache
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.local_store_id = local_store_id
        self.price_history = price_history_service

        self.deal_engine = DealEngine()
        self.deal_ranker = DealRanker()
        self.store_discovery = StoreDiscoveryService(client)

        # Concurrency bounds: 3 geo-probes + 5 product checks simultaneously
        self.discovery_sem = asyncio.Semaphore(3)
        self.product_check_sem = asyncio.Semaphore(5)

    # ------------------------------------------------------------------ helpers

    async def _async_product_at_store(self, store_id: str, external_product_id: str) -> Optional[InstamartProduct]:
        async with self.product_check_sem:
            return await asyncio.to_thread(product_at_store, self.client, store_id, external_product_id)

    async def _async_search_store(self, store_id: str, query: str) -> List[InstamartProduct]:
        async with self.product_check_sem:
            return await asyncio.to_thread(search, self.client, store_id, query)

    async def _async_discover_store(self, lat: float, lng: float) -> Optional[Store]:
        async with self.discovery_sem:
            return await asyncio.to_thread(self.store_discovery.discover_store, lat, lng)

    def _record_and_evaluate(
        self,
        product: InstamartProduct,
        store_id: str,
        condition: Optional[DealCondition],
    ):
        history_context = None
        if self.price_history:
            obs = self.price_history.record_observation(product, store_id)
            history_context = self.price_history.get_history_context(product, store_id, obs)
        return self.deal_engine.evaluate(product, condition, history_context)

    async def _probe_and_populate_cache(
        self, search_id: str, center_lat: float, center_lng: float,
        radius_km: float
    ) -> AsyncIterator[Dict]:
        """Hex-grid probe → discover stores → upsert into cache. Yields SSE events."""
        probes = HexGridGenerator.generate(center_lat, center_lng, radius_km, spacing_km=1.5)
        yield {"event": "probe_started", "search_id": search_id, "data": {"count": len(probes)}}

        discovery_tasks = [self._async_discover_store(lat, lng) for lat, lng in probes]
        discovered = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        for i, store in enumerate(discovered):
            if isinstance(store, Exception):
                log.error("Store discovery failed for probe %s: %s", probes[i], store)
                continue
            if store is None:
                continue
            cached = self.store_cache.upsert_store(store)
            yield {
                "event": "store_discovered",
                "search_id": search_id,
                "data": {
                    "store_id": cached.external_store_id,
                    "lat": cached.lat,
                    "lng": cached.lng,
                    "name": cached.name,
                },
            }
        yield {"event": "probe_completed", "search_id": search_id, "data": {}}

    # ------------------------------------------------------------------ main search

    async def run_search(
        self,
        search_id: str,
        keyword: str,
        match_keywords: List[str] = None,
        exclude_keywords: List[str] = None,
        condition: DealCondition = None,
        expansion_radii_km: List[float] = None,
        strategy: str = "NEARBY_FIRST",
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncIterator[Dict]:
        """
        Keyword/category search → local check → geo expansion.
        Yields SSE-ready event dicts.
        """
        if expansion_radii_km is None:
            expansion_radii_km = [3.0, 5.0, 10.0]

        # Server-side 20km safety clamp
        expansion_radii_km = [min(r, self.MAX_SEARCH_RADIUS_KM) for r in expansion_radii_km]
        expansion_radii_km = list(dict.fromkeys(expansion_radii_km))

        yield {"event": "search_started", "search_id": search_id, "data": {"keyword": keyword, "search_mode": "keyword"}}

        scanned_store_ids: Set[str] = set()
        total_deals = 0

        # ── STAGE 1: LOCAL SEARCH ─────────────────────────────────────────────
        if cancel_event and cancel_event.is_set():
            yield {"event": "search_cancelled", "search_id": search_id, "data": {"message": "Cancelled by user."}}
            return

        yield {"event": "local_search_started", "search_id": search_id, "data": {"store_id": self.local_store_id}}

        discovery = ProductDiscoveryEngine(self.client, self.local_store_id)
        canonical_candidates = await asyncio.to_thread(
            discovery.discover, keyword, match_keywords, exclude_keywords
        )

        if not canonical_candidates:
            yield {
                "event": "search_error",
                "search_id": search_id,
                "data": {"message": f"No relevant products found for '{keyword}'"},
            }
            return

        yield {
            "event": "product_discovered",
            "search_id": search_id,
            "data": {
                "count": len(canonical_candidates),
                "candidates": [c.normalized_name for c in canonical_candidates],
            },
        }

        local_deals_flat = []
        local_store_obj = self.store_cache.get_store(self.local_store_id)
        if local_store_obj is None:
            local_store_obj = Store(
                external_store_id=self.local_store_id,
                platform="instamart",
                lat=self.center_lat,
                lng=self.center_lng,
                distance_km=0.0,
            )

        for canonical in canonical_candidates:
            if cancel_event and cancel_event.is_set():
                yield {"event": "search_cancelled", "search_id": search_id, "data": {"message": "Cancelled."}}
                return

            external_id = canonical.id.replace("canonical_", "")
            try:
                product = await self._async_product_at_store(self.local_store_id, external_id)
                if product is None or not product.stock:
                    continue
                eval_result = self._record_and_evaluate(product, self.local_store_id, condition)
                if eval_result.qualifies:
                    deal_data = _build_deal_event(product, self.local_store_id, local_store_obj, eval_result)
                    local_deals_flat.append(deal_data["_flat"])
                    total_deals += 1
                    yield {"event": "deal_found", "search_id": search_id, "data": deal_data}
            except Exception as e:
                log.error("Local targeted fetch failed for %s: %s", external_id, e)
                yield {
                    "event": "product_check_failed",
                    "search_id": search_id,
                    "data": {"store_id": self.local_store_id, "product_id": external_id, "error": str(e)},
                }

        scanned_store_ids.add(self.local_store_id)
        yield {"event": "local_search_completed", "search_id": search_id, "data": {"deals_found": len(local_deals_flat)}}

        if local_deals_flat and strategy == "NEARBY_FIRST":
            yield {
                "event": "search_completed",
                "search_id": search_id,
                "data": {"message": "Deals found locally. Stopping early (NEARBY_FIRST).", "total_deals": total_deals},
            }
            return

        # ── STAGE 2: GEOGRAPHIC EXPANSION ────────────────────────────────────
        yield {"event": "radius_expansion_started", "search_id": search_id, "data": {"radii": expansion_radii_km}}

        for radius in expansion_radii_km:
            if cancel_event and cancel_event.is_set():
                yield {"event": "search_cancelled", "search_id": search_id, "data": {"message": "Cancelled."}}
                return

            yield {"event": "radius_scan_started", "search_id": search_id, "data": {"radius_km": radius}}

            async for probe_event in self._probe_and_populate_cache(
                search_id, self.center_lat, self.center_lng, radius
            ):
                yield probe_event

            stores_in_radius = self.store_cache.stores_within(self.center_lat, self.center_lng, radius)
            stores_to_scan = [s for s in stores_in_radius if s.external_store_id not in scanned_store_ids]

            if stores_to_scan:
                yield {"event": "store_scan_started", "search_id": search_id, "data": {"stores_count": len(stores_to_scan)}}

            radius_deals = 0
            for store in stores_to_scan:
                if cancel_event and cancel_event.is_set():
                    yield {"event": "search_cancelled", "search_id": search_id, "data": {"message": "Cancelled."}}
                    return

                scanned_store_ids.add(store.external_store_id)

                check_tasks = []
                id_map: Dict[str, CanonicalProduct] = {}
                for canonical in canonical_candidates:
                    external_id = canonical.id.replace("canonical_", "")
                    id_map[external_id] = canonical
                    check_tasks.append(self._async_product_at_store(store.external_store_id, external_id))

                yield {
                    "event": "product_check_started",
                    "search_id": search_id,
                    "data": {"store_id": store.external_store_id, "count": len(check_tasks)},
                }
                products = await asyncio.gather(*check_tasks, return_exceptions=True)
                yield {"event": "product_check_completed", "search_id": search_id, "data": {"store_id": store.external_store_id}}

                for product in products:
                    if isinstance(product, Exception):
                        log.error("Product check failed at %s: %s", store.external_store_id, product)
                        yield {
                            "event": "store_scan_failed",
                            "search_id": search_id,
                            "data": {"store_id": store.external_store_id, "error": str(product)},
                        }
                        continue
                    if product is None or not product.stock:
                        continue

                    eval_result = self._record_and_evaluate(product, store.external_store_id, condition)
                    if eval_result.qualifies:
                        deal_data = _build_deal_event(product, store.external_store_id, store, eval_result)
                        radius_deals += 1
                        total_deals += 1
                        yield {"event": "deal_found", "search_id": search_id, "data": deal_data}

            yield {
                "event": "radius_completed",
                "search_id": search_id,
                "data": {"radius_km": radius, "deals_found": radius_deals},
            }

            if radius_deals > 0 and strategy == "NEARBY_FIRST":
                yield {
                    "event": "search_completed",
                    "search_id": search_id,
                    "data": {
                        "message": f"Deals found at {radius}km. Stopping early (NEARBY_FIRST).",
                        "total_deals": total_deals,
                    },
                }
                return

        yield {
            "event": "search_completed",
            "search_id": search_id,
            "data": {"message": "Maximum radius reached.", "total_deals": total_deals},
        }

    # ------------------------------------------------------------------ URL/wishlist search

    async def run_url_search(
        self,
        search_id: str,
        product_urls: List[str],
        condition: DealCondition = None,
        expansion_radii_km: List[float] = None,
        strategy: str = "NEARBY_FIRST",
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncIterator[Dict]:
        """
        Exact product URL / wishlist search.
        Resolves each URL to a product ID, checks local store, then expands geographically.
        """
        if expansion_radii_km is None:
            expansion_radii_km = [3.0, 5.0, 10.0]

        expansion_radii_km = [min(r, self.MAX_SEARCH_RADIUS_KM) for r in expansion_radii_km]
        expansion_radii_km = list(dict.fromkeys(expansion_radii_km))

        # Resolve URLs → product IDs
        product_ids: List[str] = []
        for url in product_urls:
            pid = _extract_product_id(url)
            if pid:
                product_ids.append(pid)
            else:
                log.warning("Could not extract product ID from URL: %s", url)

        if not product_ids:
            yield {
                "event": "search_error",
                "search_id": search_id,
                "data": {"message": "No valid Instamart product URLs provided."},
            }
            return

        yield {
            "event": "search_started",
            "search_id": search_id,
            "data": {"keyword": f"{len(product_ids)} product(s)", "search_mode": "url_wishlist", "product_ids": product_ids},
        }

        scanned_store_ids: Set[str] = set()
        total_deals = 0

        # ── STAGE 1: LOCAL CHECK ──────────────────────────────────────────────
        yield {"event": "local_search_started", "search_id": search_id, "data": {"store_id": self.local_store_id}}

        local_store_obj = self.store_cache.get_store(self.local_store_id)
        if local_store_obj is None:
            local_store_obj = Store(
                external_store_id=self.local_store_id,
                platform="instamart",
                lat=self.center_lat,
                lng=self.center_lng,
                distance_km=0.0,
            )

        local_tasks = [self._async_product_at_store(self.local_store_id, pid) for pid in product_ids]
        local_products = await asyncio.gather(*local_tasks, return_exceptions=True)

        local_deal_count = 0
        for product in local_products:
            if isinstance(product, Exception) or product is None:
                continue
            eval_result = self._record_and_evaluate(product, self.local_store_id, condition)
            if eval_result.qualifies:
                deal_data = _build_deal_event(product, self.local_store_id, local_store_obj, eval_result)
                local_deal_count += 1
                total_deals += 1
                yield {"event": "deal_found", "search_id": search_id, "data": deal_data}

        scanned_store_ids.add(self.local_store_id)
        yield {"event": "local_search_completed", "search_id": search_id, "data": {"deals_found": local_deal_count}}

        if local_deal_count > 0 and strategy == "NEARBY_FIRST":
            yield {
                "event": "search_completed",
                "search_id": search_id,
                "data": {"message": "Deals found locally. Stopping early.", "total_deals": total_deals},
            }
            return

        # ── STAGE 2: GEOGRAPHIC EXPANSION ────────────────────────────────────
        yield {"event": "radius_expansion_started", "search_id": search_id, "data": {"radii": expansion_radii_km}}

        for radius in expansion_radii_km:
            if cancel_event and cancel_event.is_set():
                yield {"event": "search_cancelled", "search_id": search_id, "data": {"message": "Cancelled."}}
                return

            yield {"event": "radius_scan_started", "search_id": search_id, "data": {"radius_km": radius}}

            async for probe_event in self._probe_and_populate_cache(
                search_id, self.center_lat, self.center_lng, radius
            ):
                yield probe_event

            stores_in_radius = self.store_cache.stores_within(self.center_lat, self.center_lng, radius)
            stores_to_scan = [s for s in stores_in_radius if s.external_store_id not in scanned_store_ids]

            if stores_to_scan:
                yield {"event": "store_scan_started", "search_id": search_id, "data": {"stores_count": len(stores_to_scan)}}

            radius_deals = 0
            for store in stores_to_scan:
                if cancel_event and cancel_event.is_set():
                    yield {"event": "search_cancelled", "search_id": search_id, "data": {"message": "Cancelled."}}
                    return

                scanned_store_ids.add(store.external_store_id)

                check_tasks = [self._async_product_at_store(store.external_store_id, pid) for pid in product_ids]
                yield {
                    "event": "product_check_started",
                    "search_id": search_id,
                    "data": {"store_id": store.external_store_id, "count": len(check_tasks)},
                }
                products = await asyncio.gather(*check_tasks, return_exceptions=True)
                yield {"event": "product_check_completed", "search_id": search_id, "data": {"store_id": store.external_store_id}}

                for product in products:
                    if isinstance(product, Exception) or product is None:
                        continue
                    eval_result = self._record_and_evaluate(product, store.external_store_id, condition)
                    if eval_result.qualifies:
                        deal_data = _build_deal_event(product, store.external_store_id, store, eval_result)
                        radius_deals += 1
                        total_deals += 1
                        yield {"event": "deal_found", "search_id": search_id, "data": deal_data}

            yield {
                "event": "radius_completed",
                "search_id": search_id,
                "data": {"radius_km": radius, "deals_found": radius_deals},
            }

            if radius_deals > 0 and strategy == "NEARBY_FIRST":
                yield {
                    "event": "search_completed",
                    "search_id": search_id,
                    "data": {"message": f"Deals found at {radius}km.", "total_deals": total_deals},
                }
                return

        yield {
            "event": "search_completed",
            "search_id": search_id,
            "data": {"message": "Maximum radius reached.", "total_deals": total_deals},
        }
