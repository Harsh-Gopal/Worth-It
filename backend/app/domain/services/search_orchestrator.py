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
from typing import AsyncIterator, List, Dict, Set, Optional, Any
from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass

@dataclass
class _DiscoveredStore:
    store_id: str
    store_name: str
    probe_lat: float
    probe_lng: float

import httpx

from app.domain.models.deal import DealCondition
from app.domain.models.alert import AlertRule
from app.domain.models.product import CanonicalProduct, InstamartProduct
from app.domain.models.store import Store
from app.domain.services.product_discovery import ProductDiscoveryEngine
from app.domain.services.deal_engine import DealEngine
from app.domain.services.deal_ranker import DealRanker
from app.geo.store_cache import StoreCache
from app.grid import hex_grid
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
    origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None,
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
            "pincode": store.pincode if store else None,
        },
        "discount_percent": eval_result.discount_percent,
        "price_drop_percent": eval_result.price_drop_percent,
        "historical_low_before_now": eval_result.historical_low,
        "is_historical_low": eval_result.is_historical_low,
        "trigger_reasons": eval_result.trigger_reasons,
        
        "deal_level": eval_result.deal_level,
        "deal_score": eval_result.deal_score,
        "savings_amount": eval_result.savings_amount,
        "applicable_rule": eval_result.applicable_rule,
        
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
            "store_pincode": store.pincode if store else None,
            "origin_lat": origin_lat,
            "origin_lng": origin_lng,
            "deal_level": eval_result.deal_level,
            "deal_score": eval_result.deal_score,
            "savings_amount": eval_result.savings_amount,
            "applicable_rule": eval_result.applicable_rule,
        }
    }


class DealSearchOrchestrator:

    # ------------------------------------------------------------------ COMBINED SEARCH

    async def run_combined_search(
        self,
        search_id: str,
        keyword: str,
        product_urls: List[str],
        match_keywords: List[str] = None,
        exclude_keywords: List[str] = None,
        condition: DealCondition = None,
        expansion_radii_km: List[float] = None,
        strategy: str = "NEARBY_FIRST",
        cancel_event: Optional[asyncio.Event] = None,
        rule: Optional[AlertRule] = None,
        target_type: str = "keyword",
    ) -> AsyncIterator[Dict]:
        """
        Unified search that simultaneously checks wishlist URLs and performs keyword discovery.
        """
        if expansion_radii_km is None:
            expansion_radii_km = [3.0, 5.0, 10.0]

        expansion_radii_km = [min(r, self.MAX_SEARCH_RADIUS_KM) for r in expansion_radii_km]
        expansion_radii_km = list(dict.fromkeys(expansion_radii_km))

        # 1. Resolve URLs
        product_ids = []
        if product_urls:
            for url in product_urls:
                pid = _extract_product_id(url)
                if pid:
                    product_ids.append(pid)

        yield {
            "event": "search_started",
            "search_id": search_id,
            "data": {
                "keyword": keyword, 
                "search_mode": "keyword",
                "type": target_type,
                "product_ids": product_ids
            }
        }

        scanned_store_ids: Set[str] = set()
        seen_deals: Set[str] = set() # For deduplication
        total_deals = 0

        # Compute once — used in both local search and geo-expansion stages.
        # Search each keyword independently (OR semantics): "coconut chocolate"
        # returns 0 results; separate "coconut" and "chocolate" queries return real products.
        search_keywords = match_keywords if match_keywords else ([keyword] if keyword else [])

        # Helper to process products
        def _process_product(product, store_id, source="discovery"):
            nonlocal total_deals
            if not product or not product.stock:
                return None

            dedup_key = f"{store_id}:{product.external_product_id}"
            if dedup_key in seen_deals:
                return None

            # Wishlist matches get a boost implicitly by source flag
            if match_keywords and source != "wishlist":
                name_lower = product.name.lower()
                # Use substring match: "chocolate" matches "chocolate cake mix"
                # Also handle plural/root: "chocolates" -> try "chocolate" too
                def _kw_matches(kw: str, name: str) -> bool:
                    kw_lower = kw.lower()
                    if kw_lower in name:
                        return True
                    # Try stripping trailing 's' for basic plural handling
                    if kw_lower.endswith("s") and kw_lower[:-1] in name:
                        return True
                    return False
                if not any(_kw_matches(mk, name_lower) for mk in match_keywords):
                    return None
            if exclude_keywords and source != "wishlist":
                if any(ek.lower() in product.name.lower() for ek in exclude_keywords):
                    return None

            eval_result = self._record_and_evaluate(product, store_id, condition, rule)
            if eval_result.qualifies:
                seen_deals.add(dedup_key)
                deal_data = _build_deal_event(product, store_id, None, eval_result, self.center_lat, self.center_lng)
                deal_data["source"] = source
                total_deals += 1
                return deal_data
            return None

        # STAGE 1: LOCAL SEARCH
        if self.local_store_id:
            yield {"event": "local_search_started", "search_id": search_id, "data": {"store_id": self.local_store_id}}
            scanned_store_ids.add(self.local_store_id)

            tasks = []
            for kw in search_keywords:
                tasks.append(self._async_search_store(self.local_store_id, kw))
            for pid in product_ids:
                tasks.append(self._async_product_at_store(self.local_store_id, pid))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            n_kw_tasks = len(search_keywords)
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    log.error("Error in LOCAL SEARCH task %d: %s", i, res, exc_info=False)
                    continue
                # First n_kw_tasks are keyword searches (discovery), rest are wishlist URL checks
                source = "wishlist" if i >= n_kw_tasks else "discovery"
                items = res if isinstance(res, list) else [res]
                for item in items:
                    deal = _process_product(item, self.local_store_id, source=source)
                    if deal:
                        yield {"event": "deal_found", "search_id": search_id, "data": deal}

            yield {"event": "local_search_completed", "search_id": search_id, "data": {"store_id": self.local_store_id}}

        # STAGE 2: GEO EXPANSION
        for radius in expansion_radii_km:
            if cancel_event and cancel_event.is_set():
                break
                
            yield {"event": "radius_started", "search_id": search_id, "data": {"radius_km": radius}}
            
            stores_in_radius = []
            async for probe_event in self._probe_and_populate_cache(search_id, self.center_lat, self.center_lng, radius):
                if probe_event["event"] == "store_discovered":
                    stores_in_radius.append(probe_event["data"]["store_id"])
                yield probe_event
                
            stores_to_scan = [sid for sid in stores_in_radius if sid not in scanned_store_ids]
            
            if not stores_to_scan:
                yield {"event": "radius_completed", "search_id": search_id, "data": {"radius_km": radius, "deals_found": 0}}
                continue
                
            radius_deals = 0
            for sid in stores_to_scan:
                if cancel_event and cancel_event.is_set():
                    break
                    
                scanned_store_ids.add(sid)
                yield {"event": "product_check_started", "search_id": search_id, "data": {"store_id": sid, "count": len(product_ids) + len(search_keywords)}}

                tasks = []
                for kw in search_keywords:
                    tasks.append(self._async_search_store(sid, kw))
                for pid in product_ids:
                    tasks.append(self._async_product_at_store(sid, pid))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, res in enumerate(results):
                    if isinstance(res, Exception):
                        log.error("Error in RADIUS SEARCH task %d at %s: %s", i, sid, res)
                        continue
                    source = "wishlist" if i >= len(search_keywords) else "discovery"
                    items = res if isinstance(res, list) else [res]
                    for item in items:
                        deal = _process_product(item, sid, source=source)
                        if deal:
                            radius_deals += 1
                            yield {"event": "deal_found", "search_id": search_id, "data": deal}
                            
                yield {"event": "product_check_completed", "search_id": search_id, "data": {"store_id": sid}}
                
            yield {"event": "radius_completed", "search_id": search_id, "data": {"radius_km": radius, "deals_found": radius_deals}}
            
            if radius_deals > 0 and strategy == "NEARBY_FIRST":
                yield {"event": "search_completed", "search_id": search_id, "data": {"message": f"Deals found at {radius}km.", "total_deals": total_deals}}
                return

        yield {"event": "search_completed", "search_id": search_id, "data": {"message": "Maximum radius reached.", "total_deals": total_deals}}

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

        # Concurrency bounds: 3 geo-probes + 5 product checks simultaneously
        self.discovery_sem = asyncio.Semaphore(3)
        self.product_check_sem = asyncio.Semaphore(5)

    # ------------------------------------------------------------------ helpers

    async def _async_product_at_store(self, store_id: str, external_product_id: str) -> Optional[InstamartProduct]:
        async with self.product_check_sem:
            if hasattr(self.client, "product_at_store"):
                res = await self.client.product_at_store(external_product_id, store_id, self.center_lat, self.center_lng)
                if not res: return None
                return InstamartProduct(
                    external_product_id=res.external_product_id,
                    name=res.name,
                    url="",
                    price=res.price,
                    mrp=res.mrp,
                    stock=True,
                    image_url=res.image_url,
                    canonical_product_id=None,
                    category=""
                )
            return None

    async def _async_search_store(self, store_id: str, query: str) -> List[InstamartProduct]:
        async with self.product_check_sem:
            if not hasattr(self.client, "search"):
                log.warning("_async_search_store: client has no search() method")
                return []
            results = await self.client.search(query, store_id, self.center_lat, self.center_lng)
            out = []
            for res in results:
                if not res.name:
                    continue
                # Require a valid external_product_id for dedup; use name+price as fallback
                ext_id = res.external_product_id or f"synthetic_{res.name}_{res.price}"
                out.append(InstamartProduct(
                    external_product_id=ext_id,
                    name=res.name,
                    url=f"https://www.swiggy.com/instamart/item/{ext_id}" if res.external_product_id else "",
                    price=res.price or 0.0,
                    mrp=res.mrp or res.price or 0.0,
                    stock=(res.status == "in_stock"),
                    image_url=res.image_url,
                    canonical_product_id=None,
                    category="",
                ))
            log.info("_async_search_store: store=%s query='%s' → %d products", store_id, query, len(out))
            return out



    async def _async_discover_store(self, lat: float, lng: float):
        async with self.discovery_sem:
            try:
                res = await self.client.resolve_store(lat, lng)
                if res and res.store_id:
                    return _DiscoveredStore(store_id=res.store_id, store_name=res.store_name, probe_lat=lat, probe_lng=lng)
                return None
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"resolve_store failed: {e}")
                return None

    def _record_and_evaluate(
        self,
        product: InstamartProduct,
        store_id: str,
        condition: Optional[DealCondition],
        rule: Optional[Any] = None,
    ):
        history_context = None
        if self.price_history:
            obs = self.price_history.record_observation(product, store_id)
            history_context = self.price_history.get_history_context(product, store_id, obs)
        return self.deal_engine.evaluate(product, condition, history_context, rule)

    async def _probe_and_populate_cache(
        self, search_id: str, center_lat: float, center_lng: float,
        radius_km: float
    ) -> AsyncIterator[Dict]:
        """Hex-grid probe → discover stores → upsert into cache. Yields SSE events."""
        probes = hex_grid(center_lat, center_lng, radius_km, spacing_km=1.5)
        yield {"event": "probe_started", "search_id": search_id, "data": {"count": len(probes)}}

        discovery_tasks = [self._async_discover_store(lat, lng) for lat, lng in probes]
        discovered = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        for i, store in enumerate(discovered):
            if isinstance(store, Exception):
                log.error("Store discovery failed for probe %s: %s", probes[i], store)
                continue
            if store is None:
                continue
            cached = self.store_cache.record_probe(
                lat=store.probe_lat,
                lng=store.probe_lng,
                store_id=store.store_id,
                store_name=store.store_name,
                city=None,
                platform="instamart",
            )
            yield {
                "event": "store_discovered",
                "search_id": search_id,
                "data": {
                    "store_id": cached.id if cached else store.store_id,
                    "lat": store.probe_lat,
                    "lng": store.probe_lng,
                    "name": store.store_name,
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

        yield {"event": "search_started", "search_id": search_id, "data": {"keyword": keyword, "search_mode": "keyword", "type": "keyword", "query": keyword}}

        scanned_store_ids: Set[str] = set()
        total_deals = 0

        # ── STAGE 1: LOCAL SEARCH ─────────────────────────────────────────────
        if cancel_event and cancel_event.is_set():
            yield {"event": "search_cancelled", "search_id": search_id, "data": {"message": "Cancelled by user."}}
            return

        yield {"event": "local_search_started", "search_id": search_id, "data": {"store_id": self.local_store_id}}

        discovery = ProductDiscoveryEngine(self.client, self.local_store_id)
        canonical_candidates = await discovery.discover(keyword, match_keywords, exclude_keywords)

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
                eval_result = self._record_and_evaluate(product, self.local_store_id, condition, None)
                if eval_result.qualifies:
                    deal_data = _build_deal_event(product, self.local_store_id, local_store_obj, eval_result, self.center_lat, self.center_lng)
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

            stores_in_radius = self.store_cache.stores_within(self.center_lat, self.center_lng, radius, platform="instamart")
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

                    eval_result = self._record_and_evaluate(product, store.external_store_id, condition, None)
                    if eval_result.qualifies:
                        deal_data = _build_deal_event(product, store.external_store_id, store, eval_result, self.center_lat, self.center_lng)
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
        rule: Optional[AlertRule] = None,
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
            "data": {"keyword": f"{len(product_ids)} product(s)", "search_mode": "url_wishlist", "product_ids": product_ids, "type": "wishlist", "count": len(product_ids)},
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
            eval_result = self._record_and_evaluate(product, self.local_store_id, condition, rule)
            if eval_result.qualifies:
                deal_data = _build_deal_event(product, self.local_store_id, local_store_obj, eval_result, self.center_lat, self.center_lng)
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

            stores_in_radius = self.store_cache.stores_within(self.center_lat, self.center_lng, radius, platform="instamart")
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
                    eval_result = self._record_and_evaluate(product, store.external_store_id, condition, rule)
                    if eval_result.qualifies:
                        deal_data = _build_deal_event(product, store.external_store_id, store, eval_result, self.center_lat, self.center_lng)
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
