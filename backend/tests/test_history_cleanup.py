import pytest
from datetime import datetime, timezone, timedelta
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.domain.models.alert import AlertEvent
import uuid

def utc_now():
    return datetime.now(timezone.utc)

@pytest.fixture
def repo(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    repo = AlertRepository(db)
    return repo

def test_delete_history_by_utc_bounds(repo):
    now = utc_now()
    # Mock some dates
    d1 = now.replace(hour=10, minute=0, second=0)
    d2 = now.replace(hour=20, minute=0, second=0)
    d3 = now + timedelta(days=1)
    
    e1 = AlertEvent(id=str(uuid.uuid4()), alert_rule_id="r1", instamart_product_id="P1", platform="instamart", store_id="S1", price=100.0, mrp=100.0, discount_percent=0, trigger_reason="t", triggered_at=d1)
    e2 = AlertEvent(id=str(uuid.uuid4()), alert_rule_id="r1", instamart_product_id="P1", platform="instamart", store_id="S1", price=100.0, mrp=100.0, discount_percent=0, trigger_reason="t", triggered_at=d2)
    e3 = AlertEvent(id=str(uuid.uuid4()), alert_rule_id="r1", instamart_product_id="P1", platform="instamart", store_id="S1", price=100.0, mrp=100.0, discount_percent=0, trigger_reason="t", triggered_at=d3)
    
    repo.save_event(e1)
    repo.save_event(e2)
    repo.save_event(e3)
    
    # Let's say we want to delete events on the `now` day bounded by [d1 - 1hr, d2 + 1hr)
    start_utc = (d1 - timedelta(hours=1)).isoformat()
    end_utc = (d2 + timedelta(hours=1)).isoformat()
    
    deleted = repo.delete_history_by_utc_bounds(start_utc, end_utc)
    assert deleted == 2
    
    events = repo.get_all_events()
    assert len(events) == 1
    assert events[0].id == e3.id
