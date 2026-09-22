import asyncio
import logging
from app.platforms.swiggy import SwiggyClient
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.geo.store_cache import StoreCache
from app.domain.models.deal import DealCondition

logging.basicConfig(level=logging.INFO)

async def main():
    client = SwiggyClient(None, 5)
    lat = 25.6075768
    lng = 85.083029
    store = await client.resolve_store(lat, lng)

    cache = StoreCache("test_store_cache.db")
    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=cache,
        center_lat=lat,
        center_lng=lng,
        local_store_id=store.store_id
    )
    
    cond = DealCondition(
        max_price=None,
        price_drop_pct=None,
        require_historical_low=False,
        condition_operator="AND",
        require_in_stock=True
    )
    
    # 2. Search Coconut
    async for event in orchestrator.run_combined_search(
        search_id="test",
        keyword="Coconut",
        match_keywords=["Coconut"],
        exclude_keywords=[],
        product_urls=[],
        condition=cond,
        expansion_radii_km=[1.0]
    ):
        pass

if __name__ == "__main__":
    asyncio.run(main())
