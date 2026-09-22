import pytest
from datetime import datetime, timezone, timedelta
from app.domain.models.alert import AlertRule, AlertEvent
from app.domain.services.alert_engine import AlertEngine
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository

@pytest.fixture
def memory_db(tmp_path):
    return Database(tmp_path / "test.db")

@pytest.fixture
def alert_repo(memory_db):
    return AlertRepository(memory_db)

@pytest.fixture
def engine(alert_repo):
    return AlertEngine(alert_repo)

@pytest.fixture
def rule(alert_repo):
    r = AlertRule(
        id="rule1",
        keyword="Test",
        cooldown_hours=24.0
    )
    return alert_repo.save_rule(r)

def create_deal(price: float, discount: float, store_id: str = "store1"):
    return {
        "canonical_id": "c1",
        "instamart_product_id": "p1",
        "product_name": "Test Prod",
        "price": price,
        "mrp": 2000.0,
        "discount_pct": discount,
        "triggers": ["test"],
        "store_id": store_id,
        "distance_km": 1.0
    }

def test_alert_engine_first_observation(engine, rule):
    deal = create_deal(1000.0, 50.0)
    events = engine.evaluate_deals(rule, [deal], "test_scan_1")
    
    assert len(events) == 1
    assert events[0].price == 1000.0

def test_alert_engine_deduplication(engine, rule, alert_repo):
    # First deal triggers alert
    deal1 = create_deal(1000.0, 50.0)
    events1 = engine.evaluate_deals(rule, [deal1], "test_scan_1")
    assert len(events1) == 1
    
    # Save the event as if it was successfully sent
    alert_repo.save_event(events1[0])
    
    # Same deal immediately after -> Deduplicated (no alert)
    deal2 = create_deal(1000.0, 50.0)
    events2 = engine.evaluate_deals(rule, [deal2], "test_scan_2")
    assert len(events2) == 1
    assert events2[0].notification_status == "suppressed"

def test_alert_engine_stronger_deal_bypasses_cooldown(engine, rule, alert_repo):
    deal1 = create_deal(1000.0, 50.0)
    events1 = engine.evaluate_deals(rule, [deal1], "test_scan_1")
    alert_repo.save_event(events1[0])
    
    # Better deal -> price drops to 800
    deal2 = create_deal(800.0, 60.0)
    events2 = engine.evaluate_deals(rule, [deal2], "test_scan_2")
    assert len(events2) == 1
    assert "Better price" in events2[0].trigger_reason

def test_alert_engine_cooldown_expiration(engine, rule, alert_repo):
    deal1 = create_deal(1000.0, 50.0)
    events1 = engine.evaluate_deals(rule, [deal1], "test_scan_1")
    e1 = events1[0]
    
    # Artificially age the event beyond the 24h cooldown
    e1.triggered_at = datetime.now(timezone.utc) - timedelta(hours=25)
    alert_repo.save_event(e1)
    
    # Same deal -> Should trigger because cooldown expired
    deal2 = create_deal(1000.0, 50.0)
    events2 = engine.evaluate_deals(rule, [deal2], "test_scan_2")
    assert len(events2) == 1
    assert "Past cooldown" in events2[0].trigger_reason

def test_alert_engine_store_aware(engine, rule, alert_repo):
    # Deal at Store 1
    deal_s1 = create_deal(1000.0, 50.0, store_id="store1")
    events_s1 = engine.evaluate_deals(rule, [deal_s1], "test_scan_1")
    alert_repo.save_event(events_s1[0])
    
    # Same deal at Store 2 -> Should trigger, store-aware deduplication
    deal_s2 = create_deal(1000.0, 50.0, store_id="store2")
    events_s2 = engine.evaluate_deals(rule, [deal_s2], "test_scan_2")
    assert len(events_s2) == 1
    assert events_s2[0].store_id == "store2"
