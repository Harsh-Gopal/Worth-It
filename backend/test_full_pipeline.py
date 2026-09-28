import asyncio
import logging
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.platforms.swiggy import SwiggyClient
from app.domain.models.alert import AlertRule
from app.geo.store_cache import StoreCache
from app.domain.services.scan_context import ScanContext

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('test_pipeline')

async def run_test():
    client = SwiggyClient()
    lat = 30.7046 # Pincode 140301
    lng = 76.7179

    rule = AlertRule(
        id="test_alert",
        pincode="140301",
        adaptive_mode=True,
        keyword_rules={"Oats": {"min_discount_pct": 15.0}}
    )

    store_cache = StoreCache(path="test_stores.json")
    scan_context = ScanContext()

    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=lat,
        center_lng=lng,
        local_store_id=None,
        price_history_service=None,
        scan_context=scan_context
    )

    logger.info("Running search for 'Oats'...")

    total_deals = 0
    async for event in orchestrator.run_combined_search(
        search_id="test_scan",
        keyword="Oats",
        product_urls=[],
        match_keywords=["Oats"],
        rule=rule,
        expansion_radii_km=[3.0],
        strategy="NEARBY_FIRST",
        target_type="keyword"
    ):
        evt = getattr(event, "event", event.get("event") if isinstance(event, dict) else str(event))
        if evt == "deal_found":
            total_deals += 1
            data = getattr(event, "deal_data", event.get("data") if isinstance(event, dict) else {})
            if isinstance(data, dict):
                p = data.get("product", {})
                logger.info(f"DEAL: {p.get('name')} | MRP: {p.get('mrp')} | Price: {p.get('price')} | Discount: {data.get('discount_percent')}%")
        elif evt in ("search_started", "local_search_completed", "search_error", "search_completed", "platform_error"):
            logger.info(f"EVENT: {evt} - {getattr(event, 'data', event)}")

    logger.info(f"Total deals found: {total_deals}")

asyncio.run(run_test())
