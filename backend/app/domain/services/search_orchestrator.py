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
from app.domain.models.events import *
from app.domain.models.product import CanonicalProduct, PlatformProduct

def create_event(data_dict: dict) -> OrchestratorEvent:
    event_type = data_dict.get('event')
    payload = data_dict.get('data', {})
    payload['search_id'] = data_dict.get('search_id', '')
    mapping = {'search_started': SearchStartedEvent, 'local_search_started': LocalSearchStartedEvent, 'deal_found': DealFoundEvent, 'product_check_failed': ProductCheckFailedEvent, 'local_search_completed': LocalSearchCompletedEvent, 'radius_expansion_started': RadiusExpansionStartedEvent, 'radius_scan_started': RadiusScanStartedEvent, 'probe_started': ProbeStartedEvent, 'store_discovered': StoreDiscoveredEvent, 'probe_completed': ProbeCompletedEvent, 'store_scan_started': StoreScanStartedEvent, 'product_check_started': ProductCheckStartedEvent, 'product_check_completed': ProductCheckCompletedEvent, 'store_scan_failed': StoreScanFailedEvent, 'radius_completed': RadiusCompletedEvent, 'search_completed': SearchCompletedEvent, 'search_cancelled': SearchCancelledEvent, 'search_error': SearchErrorEvent, 'product_discovered': OrchestratorEvent, 'radius_started': RadiusScanStartedEvent}
    cls = mapping.get(event_type, OrchestratorEvent)
    if event_type == 'deal_found':
        return DealFoundEvent(search_id=payload['search_id'], deal_data=payload)
    return cls(**payload, event=event_type)
from app.domain.models.store import Store
from app.domain.services.product_discovery import ProductDiscoveryEngine
from app.domain.services.deal_engine import DealEngine
from app.domain.services.deal_ranker import DealRanker
from app.geo.store_cache import StoreCache
from app.grid import hex_grid
from app.domain.services.price_history_service import PriceHistoryService
log = logging.getLogger('orchestrator')

def _build_deal_event(product: PlatformProduct, store_id: str, store: Optional[Store], eval_result, origin_lat: Optional[float]=None, origin_lng: Optional[float]=None) -> Dict:
    """Build the canonical deal_found data payload."""
    dist = store.distance_km if store and store.distance_km is not None else 0.0
    return {'product': {'external_product_id': product.external_product_id, 'name': product.name, 'price': product.price, 'mrp': product.mrp, 'stock': product.stock, 'image_url': product.image_url, 'product_url': product.url}, 'store': {'id': store_id, 'name': store.name if store else None, 'lat': store.lat if store else None, 'lng': store.lng if store else None, 'distance_km': dist, 'pincode': store.pincode if store else None, 'platform': getattr(product, 'platform', None)}, 'discount_percent': eval_result.discount_percent, 'price_drop_percent': eval_result.price_drop_percent, 'historical_low_before_now': eval_result.historical_low, 'is_historical_low': eval_result.is_historical_low, 'trigger_reasons': eval_result.trigger_reasons, 'deal_level': eval_result.deal_level, 'deal_score': eval_result.deal_score, 'savings_amount': eval_result.savings_amount, 'applicable_rule': eval_result.applicable_rule, '_flat': {'canonical_id': product.canonical_product_id or f'canonical_{product.external_product_id}', 'instamart_product_id': product.external_product_id, 'product_name': product.name, 'price': product.price, 'mrp': product.mrp, 'discount_pct': eval_result.discount_percent, 'previous_price': eval_result.previous_price, 'price_drop_percent': eval_result.price_drop_percent, 'triggers': eval_result.trigger_reasons, 'store_id': store_id, 'distance_km': dist, 'store_pincode': store.pincode if store else None, 'origin_lat': origin_lat, 'origin_lng': origin_lng, 'deal_level': eval_result.deal_level, 'deal_score': eval_result.deal_score, 'savings_amount': eval_result.savings_amount, 'applicable_rule': eval_result.applicable_rule}}

class DealSearchOrchestrator:

    async def run_combined_search(self, search_id: str, keyword: str, product_urls: List[str], match_keywords: List[str]=None, exclude_keywords: List[str]=None, condition: DealCondition=None, expansion_radii_km: List[float]=None, strategy: str='NEARBY_FIRST', cancel_event: Optional[asyncio.Event]=None, rule: Optional[AlertRule]=None, target_type: str='keyword') -> AsyncIterator[OrchestratorEvent]:
        """
        Unified search that simultaneously checks wishlist URLs and performs keyword discovery.
        """
        if not self.local_store_id:
            try:
                res = await self.client.resolve_store(self.center_lat, self.center_lng)
                if res and res.store_id:
                    self.local_store_id = res.store_id
            except Exception as e:
                log.warning("Could not resolve local store for %s: %s", self.client.platform_name, e)
                
        if expansion_radii_km is None:
            expansion_radii_km = [3.0, 5.0, 10.0]
        expansion_radii_km = [min(r, self.MAX_SEARCH_RADIUS_KM) for r in expansion_radii_km]
        expansion_radii_km = list(dict.fromkeys(expansion_radii_km))
        product_ids = []
        if product_urls:
            for url in product_urls:
                pid = await self.client.resolve_share_link(url)
                if pid:
                    product_ids.append(pid)
        yield create_event({'event': 'search_started', 'search_id': search_id, 'data': {'keyword': keyword, 'search_mode': 'keyword', 'type': target_type, 'product_ids': product_ids}})
        scanned_store_ids: Set[str] = set()
        seen_deals: Set[str] = set()
        total_deals = 0
        search_keywords = match_keywords if match_keywords else [keyword] if keyword else []

        def _process_product(product, store_id, source='discovery'):
            nonlocal total_deals
            if not product or not product.stock:
                return None
            dedup_key = f'{store_id}:{product.external_product_id}'
            if dedup_key in seen_deals:
                return None
            if match_keywords and source != 'wishlist':
                name_lower = product.name.lower()

                def _kw_matches(kw: str, name: str) -> bool:
                    kw_lower = kw.lower()
                    if kw_lower in name:
                        return True
                    if kw_lower.endswith('s') and kw_lower[:-1] in name:
                        return True
                    return False
                if not any((_kw_matches(mk, name_lower) for mk in match_keywords)):
                    return None
            if exclude_keywords and source != 'wishlist':
                if any((ek.lower() in product.name.lower() for ek in exclude_keywords)):
                    return None
            eval_result = self._record_and_evaluate(product, store_id, condition, rule)
            if eval_result.qualifies:
                seen_deals.add(dedup_key)
                deal_data = _build_deal_event(product, store_id, None, eval_result, self.center_lat, self.center_lng)
                deal_data['source'] = source
                deal_data['store']['platform'] = self.client.platform_name
                deal_data['_flat']['platform'] = self.client.platform_name
                total_deals += 1
                return deal_data
            return None
        if self.local_store_id:
            yield create_event({'event': 'local_search_started', 'search_id': search_id, 'data': {'store_id': self.local_store_id}})
            scanned_store_ids.add(self.local_store_id)
            tasks = []
            for kw in search_keywords:
                tasks.append(self._async_search_store(self.local_store_id, kw))
            for pid in product_ids:
                tasks.append(self._async_product_at_store(self.local_store_id, pid))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            n_kw_tasks = len(search_keywords)
            for i, res in enumerate(results):
                source = 'wishlist' if i >= n_kw_tasks else 'discovery'
                if isinstance(res, Exception):
                    log.error('Error in LOCAL SEARCH task %d: %s', i, res, exc_info=False)
                    yield create_event({'event': 'search_error', 'search_id': search_id, 'data': {'message': f"Platform failed during local search: {res}"}})
                    continue
                items = res if isinstance(res, list) else [res]
                for item in items:
                    deal = _process_product(item, self.local_store_id, source=source)
                    if deal:
                        yield create_event({'event': 'deal_found', 'search_id': search_id, 'data': deal})
            yield create_event({'event': 'local_search_completed', 'search_id': search_id, 'data': {'store_id': self.local_store_id}})
        for radius in expansion_radii_km:
            if cancel_event and cancel_event.is_set():
                break
            yield create_event({'event': 'radius_started', 'search_id': search_id, 'data': {'radius_km': radius}})
            stores_in_radius = []
            async for probe_event in self._probe_and_populate_cache(search_id, self.center_lat, self.center_lng, radius):
                if probe_event['event'] == 'store_discovered':
                    stores_in_radius.append(probe_event['data']['store_id'])
                yield probe_event
            stores_to_scan = [sid for sid in stores_in_radius if sid not in scanned_store_ids]
            if not stores_to_scan:
                yield create_event({'event': 'radius_completed', 'search_id': search_id, 'data': {'radius_km': radius, 'deals_found': 0}})
                continue
            radius_deals = 0
            for sid in stores_to_scan:
                if cancel_event and cancel_event.is_set():
                    break
                scanned_store_ids.add(sid)
                yield create_event({'event': 'product_check_started', 'search_id': search_id, 'data': {'store_id': sid, 'count': len(product_ids) + len(search_keywords)}})
                tasks = []
                for kw in search_keywords:
                    tasks.append(self._async_search_store(sid, kw))
                for pid in product_ids:
                    tasks.append(self._async_product_at_store(sid, pid))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, res in enumerate(results):
                    source = 'wishlist' if i >= len(search_keywords) else 'discovery'
                    if isinstance(res, Exception):
                        log.error('Error in RADIUS SEARCH task %d at %s: %s', i, sid, res)
                        yield create_event({'event': 'search_error', 'search_id': search_id, 'data': {'message': f"Platform failed at store {sid}: {res}"}})
                        continue
                    items = res if isinstance(res, list) else [res]
                    for item in items:
                        deal = _process_product(item, sid, source=source)
                        if deal:
                            radius_deals += 1
                            yield create_event({'event': 'deal_found', 'search_id': search_id, 'data': deal})
                yield create_event({'event': 'product_check_completed', 'search_id': search_id, 'data': {'store_id': sid}})
            yield create_event({'event': 'radius_completed', 'search_id': search_id, 'data': {'radius_km': radius, 'deals_found': radius_deals}})
            if radius_deals > 0 and strategy == 'NEARBY_FIRST':
                yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': f'Deals found at {radius}km.', 'total_deals': total_deals}})
                return
        yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': 'Maximum radius reached.', 'total_deals': total_deals}})
    MAX_SEARCH_RADIUS_KM = 20.0

    def __init__(self, client: httpx.Client, store_cache: StoreCache, center_lat: float, center_lng: float, local_store_id: str, price_history_service: Optional[PriceHistoryService]=None):
        self.client = client
        self.store_cache = store_cache
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.local_store_id = local_store_id
        self.price_history = price_history_service
        self.deal_engine = DealEngine()
        self.deal_ranker = DealRanker()
        self.discovery_sem = asyncio.Semaphore(3)
        self.product_check_sem = asyncio.Semaphore(5)

    async def _async_product_at_store(self, store_id: str, external_product_id: str) -> Optional[PlatformProduct]:
        async with self.product_check_sem:
            if hasattr(self.client, 'product_at_store'):
                res = await self.client.product_at_store(external_product_id, store_id, self.center_lat, self.center_lng)
                if not res:
                    return None
                return PlatformProduct(external_product_id=res.external_product_id, name=res.name, url='', price=res.price, mrp=res.mrp, stock=True, image_url=res.image_url, canonical_product_id=None, category='')
            return None

    async def _async_search_store(self, store_id: str, query: str) -> List[PlatformProduct]:
        async with self.product_check_sem:
            if not hasattr(self.client, 'search'):
                log.warning('_async_search_store: client has no search() method')
                return []
            results = await self.client.search(query, store_id, self.center_lat, self.center_lng)
            out = []
            for res in results:
                if isinstance(res, PlatformProduct):
                    out.append(res)
                else:
                    if not res.name:
                        continue
                    ext_id = res.external_product_id or f'synthetic_{res.name}_{res.price}'
                    out.append(PlatformProduct(external_product_id=ext_id, name=res.name, category='unknown', url=f'https://www.swiggy.com/instamart/item/{ext_id}' if res.external_product_id else '', price=res.price or 0.0, mrp=res.mrp or res.price or 0.0, stock=res.status == 'in_stock', image_url=res.image_url, canonical_product_id=None))
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
                logging.getLogger(__name__).error(f'resolve_store failed: {e}')
                return None

    def _record_and_evaluate(self, product: PlatformProduct, store_id: str, condition: Optional[DealCondition], rule: Optional[Any]=None):
        history_context = None
        if self.price_history:
            obs = self.price_history.record_observation(product, store_id)
            history_context = self.price_history.get_history_context(product, store_id, obs)
        return self.deal_engine.evaluate(product, condition, history_context, rule)

    async def _probe_and_populate_cache(self, search_id: str, center_lat: float, center_lng: float, radius_km: float) -> AsyncIterator[OrchestratorEvent]:
        """Hex-grid probe → discover stores → upsert into cache. Yields SSE events."""
        probes = hex_grid(center_lat, center_lng, radius_km, spacing_km=1.5)
        yield create_event({'event': 'probe_started', 'search_id': search_id, 'data': {'count': len(probes)}})
        discovery_tasks = [self._async_discover_store(lat, lng) for lat, lng in probes]
        discovered = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        for i, store in enumerate(discovered):
            if isinstance(store, Exception):
                log.error('Store discovery failed for probe %s: %s', probes[i], store)
                continue
            if store is None:
                continue
            cached = self.store_cache.record_probe(lat=store.probe_lat, lng=store.probe_lng, store_id=store.store_id, store_name=store.store_name, city=None, platform=self.client.platform_name)
            yield create_event({'event': 'store_discovered', 'search_id': search_id, 'data': {'store_id': cached.id if cached else store.store_id, 'lat': store.probe_lat, 'lng': store.probe_lng, 'name': store.store_name}})
        yield create_event({'event': 'probe_completed', 'search_id': search_id, 'data': {}})

    async def run_search(self, search_id: str, keyword: str, match_keywords: List[str]=None, exclude_keywords: List[str]=None, condition: DealCondition=None, expansion_radii_km: List[float]=None, strategy: str='NEARBY_FIRST', cancel_event: Optional[asyncio.Event]=None) -> AsyncIterator[OrchestratorEvent]:
        """
        Keyword/category search → local check → geo expansion.
        Yields SSE-ready event dicts.
        """
        if not self.local_store_id:
            try:
                res = await self.client.resolve_store(self.center_lat, self.center_lng)
                if res and res.store_id:
                    self.local_store_id = res.store_id
            except Exception as e:
                log.warning("Could not resolve local store for %s: %s", self.client.platform_name, e)

        if expansion_radii_km is None:
            expansion_radii_km = [3.0, 5.0, 10.0]
        expansion_radii_km = [min(r, self.MAX_SEARCH_RADIUS_KM) for r in expansion_radii_km]
        expansion_radii_km = list(dict.fromkeys(expansion_radii_km))
        yield create_event({'event': 'search_started', 'search_id': search_id, 'data': {'keyword': keyword, 'search_mode': 'keyword', 'type': 'keyword', 'query': keyword}})
        scanned_store_ids: Set[str] = set()
        total_deals = 0
        if cancel_event and cancel_event.is_set():
            yield create_event({'event': 'search_cancelled', 'search_id': search_id, 'data': {'message': 'Cancelled by user.'}})
            return
        yield create_event({'event': 'local_search_started', 'search_id': search_id, 'data': {'store_id': self.local_store_id}})
        discovery = ProductDiscoveryEngine(self.client, self.local_store_id)
        canonical_candidates = await discovery.discover(keyword, match_keywords, exclude_keywords)
        if not canonical_candidates:
            yield create_event({'event': 'search_error', 'search_id': search_id, 'data': {'message': f"No relevant products found for '{keyword}'"}})
            return
        yield create_event({'event': 'product_discovered', 'search_id': search_id, 'data': {'count': len(canonical_candidates), 'candidates': [c.normalized_name for c in canonical_candidates]}})
        local_deals_flat = []
        local_store_obj = self.store_cache.get_store(self.local_store_id)
        if local_store_obj is None:
            local_store_obj = Store(external_store_id=self.local_store_id, platform=self.client.platform_name, lat=self.center_lat, lng=self.center_lng, distance_km=0.0)
        for canonical in canonical_candidates:
            if cancel_event and cancel_event.is_set():
                yield create_event({'event': 'search_cancelled', 'search_id': search_id, 'data': {'message': 'Cancelled.'}})
                return
            external_id = canonical.id.replace('canonical_', '')
            try:
                product = await self._async_product_at_store(self.local_store_id, external_id)
                if product is None or not product.stock:
                    continue
                eval_result = self._record_and_evaluate(product, self.local_store_id, condition, None)
                if eval_result.qualifies:
                    deal_data = _build_deal_event(product, self.local_store_id, local_store_obj, eval_result, self.center_lat, self.center_lng)
                    deal_data['store']['platform'] = self.client.platform_name
                    deal_data['_flat']['platform'] = self.client.platform_name
                    local_deals_flat.append(deal_data['_flat'])
                    total_deals += 1
                    yield create_event({'event': 'deal_found', 'search_id': search_id, 'data': deal_data})
            except Exception as e:
                log.error('Local targeted fetch failed for %s: %s', external_id, e)
                yield create_event({'event': 'product_check_failed', 'search_id': search_id, 'data': {'store_id': self.local_store_id, 'product_id': external_id, 'error': str(e)}})
        scanned_store_ids.add(self.local_store_id)
        yield create_event({'event': 'local_search_completed', 'search_id': search_id, 'data': {'store_id': self.local_store_id, 'deals_found': len(local_deals_flat)}})
        if local_deals_flat and strategy == 'NEARBY_FIRST':
            yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': 'Deals found locally. Stopping early (NEARBY_FIRST).', 'total_deals': total_deals}})
            return
        yield create_event({'event': 'radius_expansion_started', 'search_id': search_id, 'data': {'radii': expansion_radii_km}})
        for radius in expansion_radii_km:
            if cancel_event and cancel_event.is_set():
                yield create_event({'event': 'search_cancelled', 'search_id': search_id, 'data': {'message': 'Cancelled.'}})
                return
            yield create_event({'event': 'radius_scan_started', 'search_id': search_id, 'data': {'radius_km': radius}})
            async for probe_event in self._probe_and_populate_cache(search_id, self.center_lat, self.center_lng, radius):
                yield probe_event
            stores_in_radius = self.store_cache.stores_within(self.center_lat, self.center_lng, radius, platform=self.client.platform_name)
            stores_to_scan = [s for s in stores_in_radius if s.external_store_id not in scanned_store_ids]
            if stores_to_scan:
                yield create_event({'event': 'store_scan_started', 'search_id': search_id, 'data': {'stores_count': len(stores_to_scan)}})
            radius_deals = 0
            for store in stores_to_scan:
                if cancel_event and cancel_event.is_set():
                    yield create_event({'event': 'search_cancelled', 'search_id': search_id, 'data': {'message': 'Cancelled.'}})
                    return
                scanned_store_ids.add(store.external_store_id)
                check_tasks = []
                id_map: Dict[str, CanonicalProduct] = {}
                for canonical in canonical_candidates:
                    external_id = canonical.id.replace('canonical_', '')
                    id_map[external_id] = canonical
                    check_tasks.append(self._async_product_at_store(store.external_store_id, external_id))
                yield create_event({'event': 'product_check_started', 'search_id': search_id, 'data': {'store_id': store.external_store_id, 'count': len(check_tasks)}})
                products = await asyncio.gather(*check_tasks, return_exceptions=True)
                yield create_event({'event': 'product_check_completed', 'search_id': search_id, 'data': {'store_id': store.external_store_id}})
                for product in products:
                    if isinstance(product, Exception):
                        log.error('Product check failed at %s: %s', store.external_store_id, product)
                        yield create_event({'event': 'store_scan_failed', 'search_id': search_id, 'data': {'store_id': store.external_store_id, 'error': str(product)}})
                        continue
                    if product is None or not product.stock:
                        continue
                    eval_result = self._record_and_evaluate(product, store.external_store_id, condition, None)
                    if eval_result.qualifies:
                        deal_data = _build_deal_event(product, store.external_store_id, store, eval_result, self.center_lat, self.center_lng)
                        radius_deals += 1
                        total_deals += 1
                        yield create_event({'event': 'deal_found', 'search_id': search_id, 'data': deal_data})
            yield create_event({'event': 'radius_completed', 'search_id': search_id, 'data': {'radius_km': radius, 'deals_found': radius_deals}})
            if radius_deals > 0 and strategy == 'NEARBY_FIRST':
                yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': f'Deals found at {radius}km. Stopping early (NEARBY_FIRST).', 'total_deals': total_deals}})
                return
        yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': 'Maximum radius reached.', 'total_deals': total_deals}})

    async def run_url_search(self, search_id: str, product_urls: List[str], condition: DealCondition=None, expansion_radii_km: List[float]=None, strategy: str='NEARBY_FIRST', cancel_event: Optional[asyncio.Event]=None, rule: Optional[AlertRule]=None) -> AsyncIterator[OrchestratorEvent]:
        """
        Exact product URL / wishlist search.
        Resolves each URL to a product ID, checks local store, then expands geographically.
        """
        if not self.local_store_id:
            try:
                res = await self.client.resolve_store(self.center_lat, self.center_lng)
                if res and res.store_id:
                    self.local_store_id = res.store_id
            except Exception as e:
                log.warning("Could not resolve local store for %s: %s", self.client.platform_name, e)

        if expansion_radii_km is None:
            expansion_radii_km = [3.0, 5.0, 10.0]
        expansion_radii_km = [min(r, self.MAX_SEARCH_RADIUS_KM) for r in expansion_radii_km]
        expansion_radii_km = list(dict.fromkeys(expansion_radii_km))
        product_ids: List[str] = []
        for url in product_urls:
            pid = await self.client.resolve_share_link(url)
            if pid:
                product_ids.append(pid)
            else:
                log.warning('Could not extract product ID from URL: %s', url)
        if not product_ids:
            yield create_event({'event': 'search_error', 'search_id': search_id, 'data': {'message': 'No valid Instamart product URLs provided.'}})
            return
        yield create_event({'event': 'search_started', 'search_id': search_id, 'data': {'keyword': f'{len(product_ids)} product(s)', 'search_mode': 'url_wishlist', 'product_ids': product_ids, 'type': 'wishlist', 'count': len(product_ids)}})
        scanned_store_ids: Set[str] = set()
        total_deals = 0
        yield create_event({'event': 'local_search_started', 'search_id': search_id, 'data': {'store_id': self.local_store_id}})
        local_store_obj = self.store_cache.get_store(self.local_store_id)
        if local_store_obj is None:
            local_store_obj = Store(external_store_id=self.local_store_id, platform=self.client.platform_name, lat=self.center_lat, lng=self.center_lng, distance_km=0.0)
        local_tasks = [self._async_product_at_store(self.local_store_id, pid) for pid in product_ids]
        local_products = await asyncio.gather(*local_tasks, return_exceptions=True)
        local_deal_count = 0
        for product in local_products:
            if isinstance(product, Exception) or product is None:
                continue
            eval_result = self._record_and_evaluate(product, self.local_store_id, condition, rule)
            if eval_result.qualifies:
                deal_data = _build_deal_event(product, self.local_store_id, local_store_obj, eval_result, self.center_lat, self.center_lng)
                deal_data['store']['platform'] = self.client.platform_name
                deal_data['_flat']['platform'] = self.client.platform_name
                local_deal_count += 1
                total_deals += 1
                yield create_event({'event': 'deal_found', 'search_id': search_id, 'data': deal_data})
        scanned_store_ids.add(self.local_store_id)
        yield create_event({'event': 'local_search_completed', 'search_id': search_id, 'data': {'store_id': self.local_store_id, 'deals_found': local_deal_count}})
        if local_deal_count > 0 and strategy == 'NEARBY_FIRST':
            yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': 'Deals found locally. Stopping early.', 'total_deals': total_deals}})
            return
        yield create_event({'event': 'radius_expansion_started', 'search_id': search_id, 'data': {'radii': expansion_radii_km}})
        for radius in expansion_radii_km:
            if cancel_event and cancel_event.is_set():
                yield create_event({'event': 'search_cancelled', 'search_id': search_id, 'data': {'message': 'Cancelled.'}})
                return
            yield create_event({'event': 'radius_scan_started', 'search_id': search_id, 'data': {'radius_km': radius}})
            async for probe_event in self._probe_and_populate_cache(search_id, self.center_lat, self.center_lng, radius):
                yield probe_event
            stores_in_radius = self.store_cache.stores_within(self.center_lat, self.center_lng, radius, platform=self.client.platform_name)
            stores_to_scan = [s for s in stores_in_radius if s.external_store_id not in scanned_store_ids]
            if stores_to_scan:
                yield create_event({'event': 'store_scan_started', 'search_id': search_id, 'data': {'stores_count': len(stores_to_scan)}})
            radius_deals = 0
            for store in stores_to_scan:
                if cancel_event and cancel_event.is_set():
                    yield create_event({'event': 'search_cancelled', 'search_id': search_id, 'data': {'message': 'Cancelled.'}})
                    return
                scanned_store_ids.add(store.external_store_id)
                check_tasks = [self._async_product_at_store(store.external_store_id, pid) for pid in product_ids]
                yield create_event({'event': 'product_check_started', 'search_id': search_id, 'data': {'store_id': store.external_store_id, 'count': len(check_tasks)}})
                products = await asyncio.gather(*check_tasks, return_exceptions=True)
                yield create_event({'event': 'product_check_completed', 'search_id': search_id, 'data': {'store_id': store.external_store_id}})
                for product in products:
                    if isinstance(product, Exception) or product is None:
                        continue
                    eval_result = self._record_and_evaluate(product, store.external_store_id, condition, rule)
                    if eval_result.qualifies:
                        deal_data = _build_deal_event(product, store.external_store_id, store, eval_result, self.center_lat, self.center_lng)
                        deal_data['store']['platform'] = self.client.platform_name
                        deal_data['_flat']['platform'] = self.client.platform_name
                        radius_deals += 1
                        total_deals += 1
                        yield create_event({'event': 'deal_found', 'search_id': search_id, 'data': deal_data})
            yield create_event({'event': 'radius_completed', 'search_id': search_id, 'data': {'radius_km': radius, 'deals_found': radius_deals}})
            if radius_deals > 0 and strategy == 'NEARBY_FIRST':
                yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': f'Deals found at {radius}km.', 'total_deals': total_deals}})
                return
        yield create_event({'event': 'search_completed', 'search_id': search_id, 'data': {'message': 'Maximum radius reached.', 'total_deals': total_deals}})