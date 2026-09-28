import pytest
import asyncio
from app.platforms.zepto.client import ZeptoClient

@pytest.mark.asyncio
async def test_zepto_probe_and_search():
    client = ZeptoClient()
    try:
        # Typical Jayanagar coordinates
        store_res = await client.resolve_store(12.9259, 77.6253)
        assert store_res is not None
        if not store_res.serviceable or not store_res.store_id:
            pytest.skip("Zepto not serviceable at this location or cookie missing")

        products = await client.search("protein", store_res.store_id, 12.9259, 77.6253)
        assert len(products) > 0
        
        # Ensure prices and mrp are parsed correctly
        for product in products:
            assert product.name is not None
            assert product.price is not None
            assert product.mrp is not None
            assert product.price <= product.mrp
    finally:
        await client.aclose()
