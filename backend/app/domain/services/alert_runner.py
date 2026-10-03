"""
Alert runner: executes a single AlertRule end-to-end.

Uses the same DealSearchOrchestrator as manual searches for identical
geographic expansion behaviour — no duplicated search architecture.
"""
import asyncio
import logging
import uuid
import httpx
from typing import List, Dict, Any

from app.domain.models.alert import AlertRule, AlertEvent
from app.geo.geocoding import nom_reverse_geocode, nom_forward
from app.domain.models.deal import DealCondition
from app.domain.services.search_orchestrator import DealSearchOrchestrator, create_event
from app.domain.services.alert_engine import AlertEngine
from app.domain.services.deal_ranker import DealRanker
from app.domain.services.price_history_service import PriceHistoryService
from app.domain.services.broadcast import broadcaster
from app.domain.services.grouping_service import ProductGroupingService
from app.persistence.repositories.alert_repo import AlertRepository
from app.notifications.provider import NotificationService
from app.geo.store_cache import StoreCache
from app.config import get_settings
from app.domain.services.scan_context import ScanContext
from app.platforms.capabilities import is_playwright_allowed

log = logging.getLogger("alert_runner")

_active_runs: Dict[str, asyncio.Event] = {}
_run_locks: Dict[str, asyncio.Lock] = {}

class AlertRunner:
    """Executes a single AlertRule end-to-end."""

    def __init__(
        self,
        alert_repo: AlertRepository,
        store_cache: StoreCache,
        price_history: PriceHistoryService,
        notification_service: NotificationService,
        clients: List[Any],  # List[PlatformClient]
        center_lat: float,
        center_lng: float,
        local_store_id: str,
    ):
        self.alert_repo = alert_repo
        self.store_cache = store_cache
        self.price_history = price_history
        self.notification_service = notification_service
        self.clients = clients
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.local_store_id = local_store_id
        self.alert_engine = AlertEngine(alert_repo)

    async def run_rule(self, rule: AlertRule) -> List[AlertEvent]:
        if rule.id not in _run_locks:
            _run_locks[rule.id] = asyncio.Lock()
            
        async with _run_locks[rule.id]:
            # Cancel any previous run for this rule
            if rule.id in _active_runs:
                _active_runs[rule.id].set()
                log.info("Cancelled previous run for alert %s", rule.id)
                # Yield to allow the previous run to detect cancellation and exit
                await asyncio.sleep(0.5)
                
            cancel_event = asyncio.Event()
            _active_runs[rule.id] = cancel_event

        try:
            return await self._run_rule_impl(rule, cancel_event)
        finally:
            if rule.id in _active_runs and _active_runs[rule.id] == cancel_event:
                del _active_runs[rule.id]
            for c in self.clients:
                try:
                    await c.aclose()
                except Exception as e:
                    log.error(f"Failed to close client {c.platform_name}: {e}")

    async def _run_rule_impl(self, rule: AlertRule, cancel_event: asyncio.Event) -> List[AlertEvent]:
        scan_run_id = str(uuid.uuid4())
        settings = get_settings()
        scan_context = ScanContext()

        lat = rule.lat if rule.lat is not None else self.center_lat
        lng = rule.lng if rule.lng is not None else self.center_lng
        store_id = rule.local_store_id if rule.local_store_id else self.local_store_id

        condition = DealCondition(
            max_price=rule.max_price,
            price_drop_pct=rule.min_price_drop_pct,
            require_historical_low=rule.require_historical_low,
            require_in_stock=rule.require_in_stock,
            condition_operator=rule.condition_operator,
        )

        search_mode = getattr(rule, "search_mode", "current_pincode")
        if search_mode == "nearby_area":
            expansion_radii = [3.0, 5.0, min(rule.radius_km, 20.0)]
            expansion_radii = list(dict.fromkeys(min(r, 20.0) for r in expansion_radii))
        else:
            expansion_radii = []

        from app.links import detect_platform
        platform_to_urls = {}
        platform_order = []
        for url in (rule.product_urls or []):
            plat = detect_platform(url)
            if plat:
                if plat not in platform_to_urls:
                    platform_to_urls[plat] = []
                    platform_order.append(plat)
                platform_to_urls[plat].append(url)

        for c in self.clients:
            if c.platform_name not in platform_order:
                platform_order.append(c.platform_name)

        total_deals_found = 0
        platform_stats = {
            c.platform_name: {
                "platform": c.platform_name,
                "status": "SUCCESS",
                "pincode": rule.pincode or getattr(self.store_cache, "pincode", None),
                "searched_keywords": rule.keywords or [],
                "searched_categories": rule.categories or [],
                "deals_found": 0,
                "message": ""
            } for c in self.clients
        }

        all_deals_flat: List[Dict[str, Any]] = []

        locations_to_scan = []
        if search_mode == "multiple_pincodes" and getattr(rule, "pincodes", []):
            for pin in rule.pincodes:
                res = await nom_forward(pin, limit=1)
                if res and len(res) > 0:
                    locations_to_scan.append({
                        "lat": float(res[0]["lat"]),
                        "lng": float(res[0]["lon"]),
                        "pincode": pin,
                        "store_id": None
                    })
        else:
            locations_to_scan.append({
                "lat": lat,
                "lng": lng,
                "pincode": getattr(rule, "pincode", None),
                "store_id": store_id
            })

        for scan_loc in locations_to_scan:
            current_lat = scan_loc["lat"]
            current_lng = scan_loc["lng"]
            current_store_id = scan_loc["store_id"]
            current_pincode = scan_loc["pincode"]
            
            # Temporary override rule pincode so event records it
            original_rule_pincode = getattr(rule, "pincode", None)
            rule.pincode = current_pincode


            queue = asyncio.Queue()
            active_tasks = []
            
            async def _consume_gen(gn, p_name):
                try:
                    async def _inner():
                        async for ev in gn:
                            ev._platform_name = p_name
                            await queue.put(ev)
                    await asyncio.wait_for(_inner(), timeout=240.0)
                except asyncio.TimeoutError:
                    log.error(f"[{p_name.upper()}] Timed out in alert runner.")
                    await queue.put(create_event({
                        "event": "platform_error", 
                        "search_id": f"alert_{rule.id}", 
                        "data": {"message": "Scan timed out for this platform.", "platform": p_name}
                    }))
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    log.error(f"Error in alert runner generator for {p_name}: {e}", exc_info=True)
                    await queue.put(create_event({
                        "event": "platform_error", 
                        "search_id": f"alert_{rule.id}", 
                        "data": {"message": str(e), "platform": p_name}
                    }))

            # Launch all platforms concurrently
            for plat_name in platform_order:
                if cancel_event.is_set():
                    break

                client = next((c for c in self.clients if c.platform_name == plat_name), None)
                if not client:
                    continue
                    
                if not is_playwright_allowed(client.platform_name, settings.playwright_enabled):
                    log.warning("[%s] skipped: requires browser (Playwright disabled)", client.platform_name)
                    platform_stats[client.platform_name]["status"] = "SKIPPED_PLAYWRIGHT_DISABLED"
                    platform_stats[client.platform_name]["message"] = "Requires browser (Playwright disabled)"
                    continue

                orchestrator = DealSearchOrchestrator(
                    client=client,
                    store_cache=self.store_cache,
                    center_lat=current_lat,
                    center_lng=current_lng,
                    local_store_id=None,
                    price_history_service=self.price_history,
                    scan_context=scan_context,
                )

                async def _run_platform(c, orch, p_name, urls):
                    try:
                        if hasattr(c, "resolve_store") and not orch.local_store_id:
                            stores_near = orch.store_cache.stores_within(current_lat, current_lng, 2.0, p_name)
                            if stores_near:
                                orch.local_store_id = stores_near[0].id
                            elif orch.store_cache.has_fresh_probe_near(current_lat, current_lng, 0.5, p_name):
                                log.info(f"[{p_name.upper()}] Location previously determined unavailable (cached). Skipping.")
                                yield create_event({'event': 'platform_unavailable', 'search_id': f"alert_{rule.id}", 'data': {'message': 'Platform is not available at this location.', 'platform': p_name}})
                                return
                            else:
                                res = await c.resolve_store(current_lat, current_lng)
                                if not res or not getattr(res, 'serviceable', True):
                                    orch.store_cache.record_probe(current_lat, current_lng, None, platform=p_name)
                                    log.info(f"[{p_name.upper()}] Location unavailable for {current_pincode}. Skipping platform scan.")
                                    yield create_event({'event': 'platform_unavailable', 'search_id': f"alert_{rule.id}", 'data': {'message': 'Platform is not available at this location.', 'platform': p_name}})
                                    return
                                if res and res.store_id:
                                    orch.local_store_id = res.store_id
                                    orch.store_cache.record_probe(current_lat, current_lng, res.store_id, store_name=getattr(res, "store_name", None), city=getattr(res, "city", None), platform=p_name)

                        # Exclude rules dictionary
                        excl_rules = rule.exclude_keyword_rules if hasattr(rule, "exclude_keyword_rules") else None

                        gens = []
                        if urls:
                            log.info("Alert %s on %s: running URL/wishlist search for %d products", rule.id, p_name, len(urls))
                            gens.append(orch.run_url_search(
                                search_id=f"alert_{rule.id}",
                                product_urls=urls,
                                condition=condition,
                                expansion_radii_km=expansion_radii,
                                strategy=rule.expansion_strategy,
                                cancel_event=cancel_event,
                                rule=rule,
                            ))

                        for target in rule.categories or []:
                            gens.append(orch.run_combined_search(
                                search_id=f"alert_{rule.id}",
                                keyword=target,
                                product_urls=[],
                                match_keywords=None,
                                exclude_keywords=rule.exclude_keywords or None,
                                exclude_keyword_rules=excl_rules,
                                condition=condition,
                                expansion_radii_km=expansion_radii,
                                strategy=rule.expansion_strategy,
                                cancel_event=cancel_event,
                                rule=rule,
                                target_type="category",
                            ))

                        for target in rule.keywords or []:
                            gens.append(orch.run_combined_search(
                                search_id=f"alert_{rule.id}",
                                keyword=target,
                                product_urls=[],
                                match_keywords=[target],
                                exclude_keywords=rule.exclude_keywords or None,
                                exclude_keyword_rules=excl_rules,
                                condition=condition,
                                expansion_radii_km=expansion_radii,
                                strategy=rule.expansion_strategy,
                                cancel_event=cancel_event,
                                rule=rule,
                                target_type="keyword",
                            ))
                            
                        for gn in gens:
                            async for ev in gn:
                                yield ev

                    except Exception as e:
                        log.error(f"[{p_name.upper()}] Technical failure: {e}", exc_info=True)
                        yield create_event({
                            "event": "platform_error", 
                            "search_id": f"alert_{rule.id}", 
                            "data": {"message": str(e), "platform": p_name}
                        })

                plat_urls = [u for u in (rule.product_urls or []) if plat_name in u]
                active_tasks.append(asyncio.create_task(_consume_gen(_run_platform(client, orchestrator, plat_name, plat_urls), plat_name)))

            async def _wait_and_close():
                if active_tasks:
                    await asyncio.gather(*active_tasks, return_exceptions=True)
                await queue.put(None)
            
            waiter = asyncio.create_task(_wait_and_close())

            while True:
                event = await queue.get()
                if event is None:
                    break
                    
                event_platform = getattr(event, "_platform_name", "unknown")

                if event.event == "search_completed":
                    total_deals_found += getattr(event, "total_deals", 0)
                    continue
                    
                if event.event == "platform_unavailable" and event_platform and event_platform in platform_stats:
                    platform_stats[event_platform]["status"] = "NOT_AVAILABLE_AT_LOCATION"
                    platform_stats[event_platform]["message"] = getattr(event, "message", "Not available at this location.")
                    await broadcaster.publish(f"alert_{rule.id}", {"event": "platform_unavailable", "data": platform_stats[event_platform]})
                    continue

                if event.event == "platform_error" and event_platform and event_platform in platform_stats:
                    platform_stats[event_platform]["status"] = "TECHNICAL_ERROR"
                    platform_stats[event_platform]["message"] = getattr(event, "message", "Technical error during scan.")
                    await broadcaster.publish(f"alert_{rule.id}", {"event": "platform_error", "data": platform_stats[event_platform]})
                    continue

                event_dict = event.model_dump(exclude={"event", "search_id", "timestamp"})
                event_dict["run_id"] = scan_run_id
                
                if event.event == "deal_found" and "deal_data" in event_dict:
                    event_dict = event_dict["deal_data"]
                    event_dict["run_id"] = scan_run_id
                    if event_platform and event_platform in platform_stats:
                        platform_stats[event_platform]["deals_found"] += 1

                await broadcaster.publish(f"alert_{rule.id}", {"event": event.event, "data": event_dict})
                if event.event == "deal_found":
                    # Extract _flat sub-dict from new nested format
                    data = getattr(event, "deal_data", {})
                    flat = data.get("_flat") or {}
                    # Supplement with product_url from product sub-dict
                    product_sub = data.get("product") or {}
                    flat["product_url"] = product_sub.get("product_url")
                    flat["product_name"] = product_sub.get("name", flat.get("product_name", ""))
                    flat["product_image"] = product_sub.get("image_url")
                    # Platform is now injected by the orchestrator
                    store_sub = data.get("store") or {}
                    flat["store_name"] = store_sub.get("name")
                    flat["distance_km"] = store_sub.get("distance_km", flat.get("distance_km"))
                    
                    # Try to extract pincodes if store obj has them, otherwise fallback
                    flat["store_pincode"] = store_sub.get("pincode", None)
                    flat["store_lat"] = store_sub.get("lat")
                    flat["store_lng"] = store_sub.get("lng")
                    # We pass rule location pincode if available
                    flat["search_pincode"] = getattr(rule, "pincode", None)
                    all_deals_flat.append(flat)

            
            rule.pincode = original_rule_pincode
# Finished scanning all platforms
        # Rank deals
        ranker = DealRanker(strategy=rule.ranking_strategy)
        ranked = ranker.rank(all_deals_flat)

        # Deduplication + cooldown + better-deal logic
        all_events = self.alert_engine.evaluate_deals(rule, ranked, scan_run_id)

        # Persist and notify only meaningful (unsuppressed) observations
        for event in all_events:
            if event.notification_status == "suppressed":
                continue

            if not event.store_pincode and event.store_lat and event.store_lng:
                try:
                    pincode = await nom_reverse_geocode(event.store_lat, event.store_lng)
                    if pincode:
                        event.store_pincode = pincode
                except Exception as e:
                    log.warning("Failed to reverse geocode store %s: %s", event.store_id, e)
            
            self.alert_repo.save_event(event)
            # Emit ALL to UI as History
            event_dict = event.model_dump()
            event_dict["triggered_at"] = event.triggered_at.isoformat()
            await broadcaster.publish(f"alert_{rule.id}", {"event": "alert_persisted", "data": event_dict})
            
            if event.notification_status != "suppressed":
                try:
                    results = await self.notification_service.notify_all(
                        event, recipient_ids=rule.telegram_recipient_ids or None
                    )
                    # update event with notification results
                    if results:
                        event.notification_attempts += 1
                        success = any(r.success for r in results)
                        event.notification_status = "sent" if success else "failed"
                        self.alert_repo.save_event(event)
                except Exception as e:
                    log.error("Notification failed for event %s: %s", event.id, e)
                    event.notification_attempts += 1
                    event.notification_status = "failed"
                    self.alert_repo.save_event(event)

        # Emit grouped events for UI based on only unsuppressed events from this scan
        unsuppressed_events = [e for e in all_events if e.notification_status != "suppressed"]
        if unsuppressed_events:
            grouped_events = ProductGroupingService.group_events(unsuppressed_events)
            import json
            for group in grouped_events:
                # Need dict with stringified datetime
                group_dict = group.model_dump()
                group_dict["triggered_at"] = group.triggered_at.isoformat()
                for o in group_dict["offers"]:
                    o["triggered_at"] = o["triggered_at"].isoformat()
                await broadcaster.publish(f"alert_{rule.id}", {"event": "alert_group_persisted", "data": group_dict})

        # Emit the final completion event manually
        await broadcaster.publish(f"alert_{rule.id}", {
            "event": "search_completed",
            "data": {
                "new_events": len(all_events),
                "total_deals": total_deals_found,
                "platforms": list(platform_stats.values())
            }
        })
        
        # Touch rule to update last scan time
        self.alert_repo.touch_rule(rule.id)

        return all_events
