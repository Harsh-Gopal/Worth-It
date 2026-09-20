"""
Alert runner: executes a single AlertRule end-to-end.

Uses the same DealSearchOrchestrator as manual searches for identical
geographic expansion behaviour — no duplicated search architecture.
"""
import asyncio
import logging
import httpx
from typing import List, Dict, Any

from app.domain.models.alert import AlertRule, AlertEvent
from app.domain.models.deal import DealCondition
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.domain.services.alert_engine import AlertEngine
from app.domain.services.deal_ranker import DealRanker
from app.domain.services.price_history_service import PriceHistoryService
from app.domain.services.broadcast import broadcaster
from app.persistence.repositories.alert_repo import AlertRepository
from app.notifications.provider import NotificationService
from app.geo.store_cache import StoreCache

log = logging.getLogger("alert_runner")


class AlertRunner:
    """Executes a single AlertRule end-to-end."""

    def __init__(
        self,
        alert_repo: AlertRepository,
        store_cache: StoreCache,
        price_history: PriceHistoryService,
        notification_service: NotificationService,
        client,  # PlatformClient or any object with search/resolve_store methods
        center_lat: float,
        center_lng: float,
        local_store_id: str,
    ):
        self.alert_repo = alert_repo
        self.store_cache = store_cache
        self.price_history = price_history
        self.notification_service = notification_service
        self.client = client
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.local_store_id = local_store_id
        self.alert_engine = AlertEngine(alert_repo)

    async def run_rule(self, rule: AlertRule) -> List[AlertEvent]:
        lat = rule.lat if rule.lat is not None else self.center_lat
        lng = rule.lng if rule.lng is not None else self.center_lng
        store_id = rule.local_store_id if rule.local_store_id else self.local_store_id

        condition = DealCondition(
            min_discount_pct=rule.min_discount_pct,
            max_price=rule.max_price,
            price_drop_pct=rule.min_price_drop_pct,
            require_historical_low=rule.require_historical_low,
            require_in_stock=rule.require_in_stock,
            condition_operator=rule.condition_operator,
        )

        orchestrator = DealSearchOrchestrator(
            client=self.client,
            store_cache=self.store_cache,
            center_lat=lat,
            center_lng=lng,
            local_store_id=store_id,
            price_history_service=self.price_history,
        )

        expansion_radii = [3.0, 5.0, min(rule.radius_km, 20.0)]
        expansion_radii = list(dict.fromkeys(min(r, 20.0) for r in expansion_radii))

        # Collect flat deal dicts from orchestrator events
        all_deals_flat: List[Dict[str, Any]] = []

        generators = []

        if rule.product_urls:
            log.info("Alert %s: running URL/wishlist search for %d products", rule.id, len(rule.product_urls))
            await broadcaster.publish(f"alert_{rule.id}", {"event": "search_started", "data": {"type": "wishlist", "count": len(rule.product_urls)}})
            generators.append(orchestrator.run_url_search(
                search_id=f"alert_{rule.id}",
                product_urls=rule.product_urls,
                condition=condition,
                expansion_radii_km=expansion_radii,
                strategy=rule.expansion_strategy,
            ))

        targets = (rule.categories or []) + (rule.keywords or [])
        if targets:
            log.info("Alert %s: running keyword searches for %d targets", rule.id, len(targets))
            for target in targets:
                await broadcaster.publish(f"alert_{rule.id}", {"event": "search_started", "data": {"type": "keyword", "query": target}})
                generators.append(orchestrator.run_combined_search(
                    search_id=f"alert_{rule.id}",
                    keyword=target,
                    product_urls=[],
                    match_keywords=[target],
                    exclude_keywords=rule.exclude_keywords or None,
                    condition=condition,
                    expansion_radii_km=expansion_radii,
                    strategy=rule.expansion_strategy,
                ))

        total_deals_found = 0

        for gen in generators:
            async for event in gen:
                if event["event"] == "search_completed":
                    total_deals_found += event.get("data", {}).get("total_deals", 0)
                    continue

                await broadcaster.publish(f"alert_{rule.id}", event)
                if event["event"] == "deal_found":
                    # Extract _flat sub-dict from new nested format
                    data = event["data"]
                    flat = data.get("_flat") or {}
                    # Supplement with product_url from product sub-dict
                    product_sub = data.get("product") or {}
                    flat["product_url"] = product_sub.get("product_url")
                    flat["product_name"] = product_sub.get("name", flat.get("product_name", ""))
                    flat["product_image"] = product_sub.get("image_url")
                    flat["platform"] = "instamart" # Currently Instamart only
                    store_sub = data.get("store") or {}
                    flat["store_name"] = store_sub.get("name")
                    flat["distance_km"] = store_sub.get("distance_km", flat.get("distance_km"))
                    
                    # Try to extract pincodes if store obj has them, otherwise fallback
                    flat["store_pincode"] = store_sub.get("pincode", None)
                    # We pass rule location pincode if available (assume it's passed or null)
                    flat["search_pincode"] = None
                    all_deals_flat.append(flat)

        # Rank deals
        ranker = DealRanker(strategy=rule.ranking_strategy)
        ranked = ranker.rank(all_deals_flat)

        # Deduplication + cooldown + better-deal logic
        new_events = self.alert_engine.evaluate_deals(rule, ranked)

        # Persist and notify
        for event in new_events:
            self.alert_repo.save_event(event)
            # Need jsonable_encoder or just dict with stringified datetime
            import json
            event_dict = event.model_dump()
            event_dict["triggered_at"] = event.triggered_at.isoformat()
            await broadcaster.publish(f"alert_{rule.id}", {"event": "alert_persisted", "data": event_dict})
            results = await self.notification_service.notify_all(
                event, recipient_ids=rule.telegram_recipient_ids or None
            )
            # update event with notification results
            if results:
                event.notification_attempts += 1
                success = any(r.success for r in results)
                event.notification_status = "sent" if success else "failed"
                self.alert_repo.save_event(event)

        # Emit the final completion event manually
        await broadcaster.publish(f"alert_{rule.id}", {
            "event": "search_completed",
            "data": {
                "new_events": len(new_events),
                "total_deals": total_deals_found
            }
        })
        
        # Touch rule to update last scan time
        self.alert_repo.touch_rule(rule.id)

        return new_events
