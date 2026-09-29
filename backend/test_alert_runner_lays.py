import asyncio
from app.domain.services.alert_runner import AlertRunner
from app.domain.models.alert import AlertRule
from app.domain.models.deal import DealCondition
from app.persistence.database import Database
from app.config import get_settings
from app.geo.store_cache import get_global_cache
from app.platforms.factory import get_platform_client
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    settings = get_settings()
    db = Database(settings.database_path)
    store_cache = get_global_cache(settings.store_cache_path)
    client = get_platform_client("swiggy")
    
    rule = AlertRule(
        id="test_rule",
        platforms=["swiggy"],
        keywords=["lays"],
        product_urls=[],  # No URLs for now
        condition=DealCondition(price_drop_pct=0.0) # Any deal
    )
    
    # Mock price history
    class DummyHistory:
        def get_price_history_context(self, *args, **kwargs):
            return {}
        def record_price(self, *args, **kwargs):
            pass
            
    class DummyNotifier:
        async def check_and_notify(self, *args, **kwargs):
            pass
            
    runner = AlertRunner(
        alert_repo=None,
        store_cache=store_cache,
        price_history=DummyHistory(),
        notification_service=DummyNotifier(),
        clients=[client],
        center_lat=12.9716,
        center_lng=77.6411,
        local_store_id=None
    )
    
    res = await runner.run_rule(rule)
    print("Found deals:", res.deals_found)
    print("Errors:", res.errors)

asyncio.run(main())
