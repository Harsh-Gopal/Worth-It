import asyncio
from app.domain.services.product_discovery import ProductDiscoveryEngine
import logging
import json

logging.basicConfig(level=logging.DEBUG)

async def test():
    # Pass None for client
    engine = ProductDiscoveryEngine(client=None, store_id='synthetic_25.60_85.08', lat=25.6075, lng=85.0830)
    payload = await engine._fetch_search_playwright("Coconut")
    print(f"Payload keys: {payload.keys()}")
    if payload:
        products = engine._parse_products(payload)
        print(f"Found {len(products)} products in payload")
        for p in products:
            print(p.name, p.price, p.mrp)
    else:
        print("Empty payload")

asyncio.run(test())
