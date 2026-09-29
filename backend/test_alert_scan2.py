import asyncio
from app.domain.services.alert_runner import AlertRunner
from app.domain.models.alert import AlertRule
from app.domain.models.deal import DealCondition
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    rule = AlertRule(
        id="test_rule",
        platforms=["swiggy"],
        keywords=["lays"],
        product_ids=[],  # No URLs for now
        condition=DealCondition(price_drop_pct=0.0) # Any deal
    )
    runner = AlertRunner()
    
    events = []
    async for event in runner._run_rule(rule):
        events.append(event)
        
    deals = [e for e in events if getattr(e, 'event', '') == 'deal_found']
    print(f"Found {len(deals)} deals!")
    if deals:
        print("First deal:", deals[0].data['product']['name'])

asyncio.run(main())
