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
                    pincode, max_price, min_price_drop_pct,
                    require_historical_low, condition_operator, require_in_stock,
                    radius_km, expansion_strategy, ranking_strategy, platforms,
                    enabled, created_at, updated_at, last_run_at, cooldown_hours,
                    lat, lng, local_store_id,
                    telegram_recipient_ids, run_interval_minutes,
                    category_rules, keyword_rules, product_rules,
                    min_savings, adaptive_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule.id,
                    rule.name,
                    json.dumps(rule.categories),
                    json.dumps(rule.keywords),
                    json.dumps(rule.exclude_keywords),
                    json.dumps(rule.product_urls),
                    rule.pincode,
                    rule.max_price,
                    rule.min_price_drop_pct,
                    int(rule.require_historical_low),
                    rule.condition_operator,
                    int(rule.require_in_stock),
                    rule.radius_km,
                    rule.expansion_strategy,
                    rule.ranking_strategy,
                    json.dumps(rule.platforms),
                    int(rule.enabled),
                    rule.created_at.isoformat(),
                    rule.updated_at.isoformat(),
                    rule.last_run_at.isoformat() if rule.last_run_at else None,
                    rule.cooldown_hours,
                    rule.lat,
                    rule.lng,
                    rule.local_store_id,
                    json.dumps(rule.telegram_recipient_ids),
                    rule.run_interval_minutes,
                    json.dumps(rule.category_rules),
                    json.dumps(rule.keyword_rules),
                    json.dumps(rule.product_rules),
                    rule.min_savings,
                    int(rule.adaptive_mode),
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

    def touch_rule(self, rule_id: str) -> None:
        """Update the updated_at timestamp to mark a successful scan."""
        with self.db.get_connection() as conn:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE alert_rules SET updated_at = ? WHERE id = ?",
                (now, rule_id)
            )
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
                    trigger_reason, triggered_at, notification_status, notification_attempts,
                    product_image, platform, store_pincode, search_pincode, origin_lat, origin_lng,
                    deal_level, deal_score, savings_amount, applicable_rule, scan_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    event.product_image,
                    event.platform,
                    event.store_pincode,
                    event.search_pincode,
                    event.origin_lat,
                    event.origin_lng,
                    event.deal_level,
                    event.deal_score,
                    event.savings_amount,
                    event.applicable_rule,
                    event.scan_run_id,
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

    def cleanup_expired_history(self, days: int = 7, tz_offset_mins: int = -330) -> int:
        """
        Deletes alert events older than `days` calendar days.
        Uses local timezone (tz_offset_mins) to determine the midnight boundary.
        """
        from datetime import datetime, timezone, timedelta
        now_utc = datetime.now(timezone.utc)
        
        # Convert UTC to local time to determine the local calendar date
        now_local = now_utc - timedelta(minutes=tz_offset_mins)
        
        # Go back `days` in local time, and set to midnight local time
        cutoff_local = (now_local - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Convert the local midnight cutoff back to UTC for database comparison
        cutoff_utc = cutoff_local + timedelta(minutes=tz_offset_mins)
        cutoff = cutoff_utc.isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM alert_events WHERE triggered_at < ?",
                (cutoff,)
            )
            conn.commit()
            return cursor.rowcount

    def delete_history_for_date(self, date_str: str) -> int:
        """Deletes alert events matching a specific date string (YYYY-MM-DD). Returns number of rows deleted."""
        with self.db.get_connection() as conn:
            # SQLite substr(triggered_at, 1, 10) extracts YYYY-MM-DD from ISO format
            cursor = conn.execute(
                "DELETE FROM alert_events WHERE substr(triggered_at, 1, 10) = ?",
                (date_str,)
            )
            conn.commit()
            return cursor.rowcount

    def delete_history_by_utc_bounds(self, start_utc: str, end_utc: str) -> int:
        """Deletes alert events strictly within the given UTC ISO datetime boundaries."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM alert_events WHERE triggered_at >= ? AND triggered_at < ?",
                (start_utc, end_utc)
            )
            conn.commit()
            return cursor.rowcount


    def get_all_events(self, limit: int = 100) -> List[AlertEvent]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM alert_events
                ORDER BY triggered_at DESC
                LIMIT ?
                """,
                (limit,),
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
            pincode=_get("pincode"),
            max_price=_get("max_price"),
            min_price_drop_pct=_get("min_price_drop_pct"),
            require_historical_low=bool(_get("require_historical_low", 0)),
            condition_operator=_get("condition_operator", "AND"),
            require_in_stock=bool(_get("require_in_stock", 1)),
            radius_km=_get("radius_km", 10.0),
            expansion_strategy=_get("expansion_strategy", "NEARBY_FIRST"),
            ranking_strategy=_get("ranking_strategy", "BEST_DISCOUNT"),
            platforms=_safe_json(_get("platforms", '["instamart"]'), ["instamart"]),
            enabled=bool(row["enabled"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
            cooldown_hours=row["cooldown_hours"],
            lat=row["lat"],
            lng=_get("lng"),
            local_store_id=_get("local_store_id"),
            telegram_recipient_ids=_safe_json(_get("telegram_recipient_ids"), []),
            run_interval_minutes=_get("run_interval_minutes", 0),
            category_rules=_safe_json(_get("category_rules"), {}),
            keyword_rules=_safe_json(_get("keyword_rules"), {}),
            product_rules=_safe_json(_get("product_rules"), {}),
            min_savings=_get("min_savings"),
            adaptive_mode=bool(_get("adaptive_mode", 1)),
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
            product_image=_get("product_image"),
            platform=_get("platform", "instamart"),
            store_pincode=_get("store_pincode"),
            search_pincode=_get("search_pincode"),
            origin_lat=_get("origin_lat"),
            origin_lng=_get("origin_lng"),
            deal_level=_get("deal_level"),
            deal_score=_get("deal_score"),
            savings_amount=_get("savings_amount"),
            applicable_rule=_get("applicable_rule"),
            scan_run_id=_get("scan_run_id"),
        )
