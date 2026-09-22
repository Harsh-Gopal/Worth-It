"""
Additional tests for spec compliance:
- Calendar-day cleanup boundary (not 7*24h)
- Deal engine keyword > category > global precedence
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.domain.models.alert import AlertEvent, AlertRule
from app.domain.services.deal_engine import DealEngine
from app.domain.models.product import PlatformProduct


def utc_now():
    return datetime.now(timezone.utc)


@pytest.fixture
def repo(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    return AlertRepository(db)


class TestCalendarDayRetention:
    def test_cleanup_keeps_records_within_7_days(self, repo):
        now = utc_now()
        six_days_ago = now - timedelta(days=6)
        e = AlertEvent(
            id=str(uuid.uuid4()), alert_rule_id="r1", instamart_product_id="P1",
            platform="instamart", store_id="S1", price=100.0, mrp=100.0,
            discount_percent=0, trigger_reason="t", triggered_at=six_days_ago
        )
        repo.save_event(e)
        deleted = repo.cleanup_expired_history(days=7)
        assert deleted == 0
        events = repo.get_all_events()
        assert len(events) == 1

    def test_cleanup_removes_records_older_than_7_days(self, repo):
        now = utc_now()
        eight_days_ago = now - timedelta(days=8)
        e = AlertEvent(
            id=str(uuid.uuid4()), alert_rule_id="r1", instamart_product_id="P1",
            platform="instamart", store_id="S1", price=100.0, mrp=100.0,
            discount_percent=0, trigger_reason="t", triggered_at=eight_days_ago
        )
        repo.save_event(e)
        deleted = repo.cleanup_expired_history(days=7)
        assert deleted == 1
        events = repo.get_all_events()
        assert len(events) == 0


class TestDealEngineRulePrecedence:
    def _make_product(self, name, price, mrp, category=None):
        return PlatformProduct(
            external_product_id="P1", url="https://example.com/p",
            name=name,
            price=price,
            mrp=mrp,
            stock=True,
            category=category,
        )

    def _make_rule(self, category_rules=None, keyword_rules=None, global_min=None):
        return AlertRule(
            id="test", name="test",
            categories=list((category_rules or {}).keys()),
            keywords=list((keyword_rules or {}).keys()),
            category_rules=category_rules or {},
            keyword_rules=keyword_rules or {},
            min_discount_pct=global_min,
            adaptive_mode=True,
        )

    def test_keyword_wins_over_category(self):
        engine = DealEngine()
        product = self._make_product("Whey Protein Chocolate", 249, 499, category="Sports & Fitness")
        rule = self._make_rule(
            category_rules={"Sports & Fitness": {"min_discount_pct": 15}},
            keyword_rules={"Whey Protein": {"min_discount_pct": 25}},
        )
        result = engine.evaluate(product, rule=rule)
        assert result.qualifies
        assert "Keyword Rule" in (result.applicable_rule or "")

    def test_keyword_fails_when_discount_below_keyword_threshold(self):
        engine = DealEngine()
        # 20% discount (399 vs 499)
        product = self._make_product("Whey Protein Chocolate", 399, 499, category="Sports & Fitness")
        rule = self._make_rule(
            category_rules={"Sports & Fitness": {"min_discount_pct": 15}},
            keyword_rules={"Whey Protein": {"min_discount_pct": 25}},
        )
        result = engine.evaluate(product, rule=rule)
        assert not result.qualifies

    def test_category_wins_over_global(self):
        engine = DealEngine()
        # 30% discount exactly (350 vs 499.x... use 350/500)
        product = self._make_product("Running Shoes", 350, 500, category="Sports & Fitness")
        rule = self._make_rule(
            category_rules={"Sports & Fitness": {"min_discount_pct": 30}},
            global_min=10,
        )
        result = engine.evaluate(product, rule=rule)
        assert result.qualifies
        assert "Category Rule" in (result.applicable_rule or "")

