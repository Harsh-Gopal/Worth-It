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

    def evaluate_deals(self, rule: AlertRule, ranked_deals: List[Dict[str, Any]]) -> List[AlertEvent]:
        new_events: List[AlertEvent] = []
        now = datetime.now(timezone.utc)

        for deal in ranked_deals:
            instamart_product_id = deal.get("instamart_product_id") or "unknown"
            canonical_id = deal.get("canonical_id")
            store_id = deal.get("store_id", "")
            price = deal.get("price", 0.0)
            mrp = deal.get("mrp", 0.0)
            discount = deal.get("discount_pct", 0.0)
            triggers: List[str] = list(deal.get("triggers", []))
            previous_price = deal.get("previous_price")
            price_drop = deal.get("price_drop_percent")
            product_name = deal.get("product_name", "")
            product_url = deal.get("product_url")
            store_name = deal.get("store_name")
            distance_km = deal.get("distance_km")

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

            if should_alert:
                event = AlertEvent(
                    id=str(uuid.uuid4()),
                    alert_rule_id=rule.id,
                    canonical_product_id=canonical_id,
                    instamart_product_id=instamart_product_id,
                    product_name=product_name,
                    product_url=product_url,
                    store_id=store_id,
                    store_name=store_name,
                    distance_km=distance_km,
                    price=price,
                    mrp=mrp,
                    discount_percent=discount,
                    previous_price=previous_price,
                    price_drop_percent=price_drop,
                    trigger_reason=", ".join(triggers),
                    triggered_at=now,
                    notification_status="pending",
                    notification_attempts=0,
                )
                new_events.append(event)

        return new_events
