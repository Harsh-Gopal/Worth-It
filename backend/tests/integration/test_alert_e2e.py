import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.domain.models.alert import AlertRule
from app.domain.services.alert_runner import AlertRunner
from app.notifications.provider import NotificationService
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.domain.services.price_history_service import PriceHistoryService
from app.persistence.repositories.price_history_repo import PriceHistoryRepository
from app.geo.store_cache import StoreCache

@pytest.fixture
def memory_db(tmp_path):
    return Database(tmp_path / "test.db")

@pytest.fixture
def alert_repo(memory_db):
    return AlertRepository(memory_db)

@pytest.fixture
def history_service(memory_db):
    return PriceHistoryService(PriceHistoryRepository(memory_db))

@pytest.fixture
def store_cache(tmp_path):
    c = StoreCache(tmp_path / "test_alert.db")
    yield c
    c.close()

@pytest.mark.asyncio
@patch("app.domain.services.alert_runner.DealSearchOrchestrator")
async def test_full_alert_e2e(
    mock_orchestrator_class,
    alert_repo,
    history_service,
    store_cache
):
    # 1. Setup Rule
    rule = AlertRule(
        id="alert_1",
        keywords=["Nutrabay protein"],
        min_discount_pct=50.0,
        radius_km=10.0
    )
    alert_repo.save_rule(rule)
    
    # 2. Mock Orchestrator to yield deals
    # Store C: ₹1899, MRP: ₹4000 -> 52.5% discount
    async def mock_run_search(*args, **kwargs):
        yield {"event": "search_started"}
        yield {
            "event": "deal_found",
            "data": {
                "product": {
                    "name": "Nutrabay protein",
                    "product_url": "url",
                },
                "store": {
                    "id": "Store C",
                    "distance_km": 5.0
                },
                "_flat": {
                    "canonical_id": "c1",
                    "instamart_product_id": "p1",
                    "product_name": "Nutrabay protein",
                    "price": 1899.0,
                    "mrp": 4000.0,
                    "discount_pct": 52.5,
                    "previous_price": None,
                    "price_drop_percent": None,
                    "triggers": ["Discount 52.5% >= 50.0%"],
                    "store_id": "Store C",
                    "distance_km": 5.0
                }
            }
        }
        yield {"event": "search_completed"}
        
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.run_combined_search.side_effect = mock_run_search
    mock_orchestrator_class.return_value = mock_orchestrator_instance
    
    # 3. Setup mocked notification provider
    mock_telegram = AsyncMock()
    mock_telegram.send_alert.return_value = MagicMock(
        success=True, provider="telegram", retryable=False, timestamp=None, error_message=None
    )
    # Fix the timestamp for the mock return
    from datetime import datetime, timezone
    mock_telegram.send_alert.return_value.timestamp = datetime.now(timezone.utc)
    
    notification_service = NotificationService([mock_telegram])
    
    # 4. Initialize Runner
    runner = AlertRunner(
        alert_repo=alert_repo,
        store_cache=store_cache,
        price_history=history_service,
        notification_service=notification_service,
        client=MagicMock(),
        center_lat=12.0,
        center_lng=77.0,
        local_store_id="local1"
    )
    
    # 5. FIRST RUN -> Should Trigger
    new_events = await runner.run_rule(rule)
    assert len(new_events) == 1
    assert mock_telegram.send_alert.call_count == 1
    
    # Verify DB state
    db_events = alert_repo.db.get_connection().execute("SELECT * FROM alert_events").fetchall()
    assert len(db_events) == 1
    assert db_events[0]["notification_status"] == "sent"
    
    # 6. SECOND RUN (Identical) -> Should Deduplicate
    new_events_2 = await runner.run_rule(rule)
    assert len(new_events_2) == 0
    assert mock_telegram.send_alert.call_count == 1 # still 1!
    
    # 7. THIRD RUN (Better Deal) -> Should Trigger
    async def mock_run_search_better(*args, **kwargs):
        yield {
            "event": "deal_found",
            "data": {
                "product": {
                    "name": "Nutrabay protein",
                    "product_url": "url",
                },
                "store": {
                    "id": "Store C",
                    "distance_km": 5.0
                },
                "_flat": {
                    "canonical_id": "c1",
                    "instamart_product_id": "p1",
                    "product_name": "Nutrabay protein",
                    "price": 1499.0, # Better price
                    "mrp": 4000.0,
                    "discount_pct": 62.5,
                    "previous_price": 1899.0,
                    "price_drop_percent": 21.0,
                    "triggers": ["Improved deal price"],
                    "store_id": "Store C",
                    "distance_km": 5.0
                }
            }
        }
        
    mock_orchestrator_instance.run_combined_search.side_effect = mock_run_search_better
    new_events_3 = await runner.run_rule(rule)
    
    assert len(new_events_3) == 1
    assert mock_telegram.send_alert.call_count == 2
    assert "Improved deal price" in new_events_3[0].trigger_reason
