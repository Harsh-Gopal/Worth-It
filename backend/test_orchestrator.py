import asyncio
import logging
import sys

logging.basicConfig(level=logging.DEBUG)

async def test():
    from app.domain.services.search_orchestrator import DealSearchOrchestrator
    from app.platforms.swiggy import SwiggyClient
    
    client = SwiggyClient()
    # Pincode 140301 -> lat=30.7544, lng=76.6545
    orchestrator = DealSearchOrchestrator(client, center_lat=30.7544, center_lng=76.6545, local_store_id="1402948")
    
    from app.domain.models.alert_rule import AlertRule
    
    rule = AlertRule(
        user_id="test",
        pincode="140301",
        keyword_rules={"Oats": {"min_discount_pct": 15}}
    )
    
    print("Running orchestrator for Oats...")
    async for event in orchestrator.run_combined_search(
        search_id="test_1",
        keyword="Oats",
        product_urls=[],
        match_keywords=["Oats"],
        rule=rule
    ):
        print(event)
        
    await client.aclose()

asyncio.run(test())
