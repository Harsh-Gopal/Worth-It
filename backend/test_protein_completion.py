import asyncio
from app.domain.models.deal import DealCondition
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.platforms.swiggy import SwiggyClient
from app.geo.store_cache import StoreCache

async def main():
    client = SwiggyClient()
    store_cache = StoreCache("data/stores.db")
    condition = DealCondition(min_discount_pct=80.0)
    orchestrator = DealSearchOrchestrator(
        client=client, store_cache=store_cache,
        center_lat=25.5809548, center_lng=85.0781589, local_store_id="synthetic_25.60_85.08"
    )
    async for event in orchestrator.run_combined_search(
        search_id="test", keyword="Protein", product_urls=[],
        match_keywords=["Protein"], condition=condition,
        expansion_radii_km=[3.0, 5.0, 10.0]
    ):
        if event["event"] == "search_completed":
            print(event)

if __name__ == "__main__":
    asyncio.run(main())
