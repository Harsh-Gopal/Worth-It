import json
import uuid
import sqlite3
from typing import List, Optional
from datetime import datetime, timezone

from app.domain.models.alert import AlertRule, AlertEvent, NotificationResult
from app.persistence.database import Database


def _safe_json(raw: str | None, default=None):
    """Safely parse a JSON string, returning default on failure."""
    if not raw:
        return default if default is not None else []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


class AlertRepository:
    def __init__(self, db: Database):
        self.db = db

    # ─── Rules ───────────────────────────────────────────────────────────────

    def save_rule(self, rule: AlertRule) -> AlertRule:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO alert_rules (
                    id, name, categories, keywords, exclude_keywords, product_urls,
                    min_discount_pct, max_price, min_price_drop_pct,
                    require_historical_low, condition_operator, require_in_stock,
                    radius_km, expansion_strategy, ranking_strategy, platform,
                    enabled, created_at, updated_at, cooldown_hours,
                    lat, lng, local_store_id,
                    telegram_recipient_ids, run_interval_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule.id,
                    rule.name,
                    json.dumps(rule.categories),
                    json.dumps(rule.keywords),
                    json.dumps(rule.exclude_keywords),
                    json.dumps(rule.product_urls),
                    rule.min_discount_pct,
                    rule.max_price,
                    rule.min_price_drop_pct,
                    int(rule.require_historical_low),
                    rule.condition_operator,
                    int(rule.require_in_stock),
                    rule.radius_km,
                    rule.expansion_strategy,
                    rule.ranking_strategy,
                    rule.platform,
                    int(rule.enabled),
                    rule.created_at.isoformat(),
                    rule.updated_at.isoformat(),
                    rule.cooldown_hours,
                    rule.lat,
                    rule.lng,
                    rule.local_store_id,
                    json.dumps(rule.telegram_recipient_ids),
                    rule.run_interval_minutes,
                ),
            )
            conn.commit()
        return rule

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM alert_rules WHERE id = ?", (rule_id,)
            ).fetchone()
            if row:
                return self._row_to_rule(row)
        return None

    def get_active_rules(self) -> List[AlertRule]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM alert_rules WHERE enabled = 1"
            ).fetchall()
            return [self._row_to_rule(r) for r in rows]

    def get_all_rules(self) -> List[AlertRule]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM alert_rules ORDER BY created_at DESC"
            ).fetchall()
            return [self._row_to_rule(r) for r in rows]

    def delete_rule(self, rule_id: str) -> None:
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
            conn.commit()

    # ─── Events ──────────────────────────────────────────────────────────────

    def save_event(self, event: AlertEvent) -> AlertEvent:
        if not event.id:
            event.id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO alert_events (
                    id, alert_rule_id, canonical_product_id, instamart_product_id,
                    product_name, product_url, store_id, store_name, distance_km,
                    price, mrp, discount_percent, previous_price, price_drop_percent,
                    trigger_reason, triggered_at, notification_status, notification_attempts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.alert_rule_id,
                    event.canonical_product_id,
                    event.instamart_product_id,
                    event.product_name,
                    event.product_url,
                    event.store_id,
                    event.store_name,
                    event.distance_km,
                    event.price,
                    event.mrp,
                    event.discount_percent,
                    event.previous_price,
                    event.price_drop_percent,
                    event.trigger_reason,
                    event.triggered_at.isoformat(),
                    event.notification_status,
                    event.notification_attempts,
                ),
            )
            conn.commit()
        return event

    def get_events_for_rule(self, rule_id: str, limit: int = 50) -> List[AlertEvent]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM alert_events
                WHERE alert_rule_id = ?
                ORDER BY triggered_at DESC
                LIMIT ?
                """,
                (rule_id, limit),
            ).fetchall()
            return [self._row_to_event(r) for r in rows]

    def get_latest_event_for_product_store(
        self, rule_id: str, instamart_product_id: str, store_id: str
    ) -> Optional[AlertEvent]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM alert_events
                WHERE alert_rule_id = ? AND instamart_product_id = ? AND store_id = ?
                ORDER BY triggered_at DESC LIMIT 1
                """,
                (rule_id, instamart_product_id, store_id),
            ).fetchone()
            if row:
                return self._row_to_event(row)
        return None

    def record_notification_attempt(self, event_id: str, result: NotificationResult) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO notification_attempts (
                    alert_event_id, success, provider, timestamp, error_message, retryable
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    int(result.success),
                    result.provider,
                    result.timestamp.isoformat(),
                    result.error_message,
                    int(result.retryable),
                ),
            )
            new_status = "sent" if result.success else "failed"
            conn.execute(
                "UPDATE alert_events SET notification_status = ?, notification_attempts = notification_attempts + 1 WHERE id = ?",
                (new_status, event_id),
            )
            conn.commit()

    # ─── Row → Model converters ───────────────────────────────────────────────

    def _row_to_rule(self, row: sqlite3.Row) -> AlertRule:
        keys = row.keys()

        def _get(k, default=None):
            return row[k] if k in keys else default

        return AlertRule(
            id=row["id"],
            name=_get("name", ""),
            categories=_safe_json(_get("categories"), []),
            keywords=_safe_json(_get("keywords"), []),
            exclude_keywords=_safe_json(_get("exclude_keywords"), []),
            product_urls=_safe_json(_get("product_urls"), []),
            min_discount_pct=_get("min_discount_pct"),
            max_price=_get("max_price"),
            min_price_drop_pct=_get("min_price_drop_pct"),
            require_historical_low=bool(_get("require_historical_low", 0)),
            condition_operator=_get("condition_operator", "AND"),
            require_in_stock=bool(_get("require_in_stock", 1)),
            radius_km=_get("radius_km", 10.0),
            expansion_strategy=_get("expansion_strategy", "NEARBY_FIRST"),
            ranking_strategy=_get("ranking_strategy", "BEST_DISCOUNT"),
            platform=_get("platform", "instamart"),
            enabled=bool(_get("enabled", 1)),
            created_at=datetime.fromisoformat(_get("created_at")),
            updated_at=datetime.fromisoformat(_get("updated_at")),
            cooldown_hours=_get("cooldown_hours", 24.0),
            lat=_get("lat"),
            lng=_get("lng"),
            local_store_id=_get("local_store_id"),
            telegram_recipient_ids=_safe_json(_get("telegram_recipient_ids"), []),
            run_interval_minutes=_get("run_interval_minutes", 0),
        )

    def _row_to_event(self, row: sqlite3.Row) -> AlertEvent:
        keys = row.keys()

        def _get(k, default=None):
            return row[k] if k in keys else default

        return AlertEvent(
            id=row["id"],
            alert_rule_id=row["alert_rule_id"],
            canonical_product_id=_get("canonical_product_id"),
            instamart_product_id=row["instamart_product_id"],
            product_name=_get("product_name", ""),
            product_url=_get("product_url"),
            store_id=row["store_id"],
            store_name=_get("store_name"),
            distance_km=_get("distance_km"),
            price=row["price"],
            mrp=row["mrp"],
            discount_percent=row["discount_percent"],
            previous_price=_get("previous_price"),
            price_drop_percent=_get("price_drop_percent"),
            trigger_reason=row["trigger_reason"],
            triggered_at=datetime.fromisoformat(row["triggered_at"]),
            notification_status=row["notification_status"],
            notification_attempts=_get("notification_attempts", 0),
        )
