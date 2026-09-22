from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid

from app.domain.models.alert import AlertRule, AlertEvent
from app.persistence.repositories.alert_repo import AlertRepository


class AlertEngine:
    """
    Deduplication, cooldown, and better-deal logic.

    For each qualifying deal:
    - First occurrence → always alert.
    - Subsequent occurrence with improved price or discount → alert immediately.
    - Subsequent occurrence past cooldown → alert again.
    - Otherwise → suppress.
    """

    def __init__(self, repo: AlertRepository):
        self.repo = repo

    def evaluate_deals(self, rule: AlertRule, ranked_deals: List[Dict[str, Any]], scan_run_id: str) -> List[AlertEvent]:
        new_events: List[AlertEvent] = []
        now = datetime.now(timezone.utc)

        for deal in ranked_deals:
            instamart_product_id = deal.get("instamart_product_id") or str(deal.get("product_id") or "unknown")
            canonical_id = deal.get("canonical_id")
            previous_price = deal.get("previous_price")
            price_drop = deal.get("price_drop_percent")
            store_id = str(deal.get("store_id") or "")
            price = deal.get("price", 0.0)
            mrp = deal.get("mrp", 0.0)
            discount = deal.get("discount_pct", 0.0)
            triggers: List[str] = list(deal.get("triggers", []))
            
            product_name = deal.get("product_name") or ""
            product_url = deal.get("product_url")
            product_image = deal.get("product_image")
            platform = deal.get("platform", "instamart")
            
            store_name = deal.get("store_name")
            store_pincode = deal.get("store_pincode")
            search_pincode = deal.get("search_pincode")
            distance_km = deal.get("distance_km")
            origin_lat = deal.get("origin_lat")
            origin_lng = deal.get("origin_lng")
            
            deal_level = deal.get("deal_level")
            deal_score = deal.get("deal_score")
            savings_amount = deal.get("savings_amount")
            applicable_rule = deal.get("applicable_rule")

            latest = self.repo.get_latest_event_for_product_store(
                rule.id, instamart_product_id, store_id
            )

            should_alert = False

            if not latest:
                should_alert = True
            else:
                hours_since = (now - latest.triggered_at).total_seconds() / 3600.0
                if price < latest.price:
                    # Price improved
                    should_alert = True
                    triggers.append(f"Better price ₹{price} < prev ₹{latest.price}")
                elif discount > latest.discount_percent:
                    # Discount improved
                    should_alert = True
                    triggers.append(f"Better discount {discount}% > prev {latest.discount_percent}%")
                elif hours_since >= rule.cooldown_hours:
                    # Past cooldown window
                    should_alert = True
                    triggers.append(f"Past cooldown ({rule.cooldown_hours}h)")

            if not should_alert:
                if not triggers:
                    triggers.append("No change since last scan")

            event = AlertEvent(
                id=str(uuid.uuid4()),
                alert_rule_id=rule.id,
                canonical_product_id=canonical_id,
                instamart_product_id=instamart_product_id,
                product_name=product_name,
                product_url=product_url,
                product_image=product_image,
                platform=platform,
                store_id=store_id,
                store_name=store_name,
                store_pincode=store_pincode,
                search_pincode=search_pincode,
                distance_km=distance_km,
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                price=price,
                mrp=mrp,
                discount_percent=discount,
                previous_price=previous_price,
                price_drop_percent=price_drop,
                trigger_reason=", ".join(triggers),
                triggered_at=now,
                notification_status="pending" if should_alert else "suppressed",
                notification_attempts=0,
                deal_level=deal_level,
                deal_score=deal_score,
                savings_amount=savings_amount,
                applicable_rule=applicable_rule,
                scan_run_id=scan_run_id,
            )
            new_events.append(event)

        return new_events
