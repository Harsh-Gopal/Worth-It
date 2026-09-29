import asyncio
from fastapi import FastAPI
from app.api.routers.product_url import lookup_product_url
from app.geo.store_cache import StoreCache
from app.persistence.database import Database
from app.config import get_settings
from app.platforms.swiggy import SwiggyClient

async def test():
    url = "https://www.zeptonow.com/pn/product/pvid/7851f4a9-cab6-4b75-bae2-bcbc43bf0bdb"
    try:
        settings = get_settings()
        db = Database(settings.database_path)
        store_cache = StoreCache(db)
        swiggy = SwiggyClient()
        res = await lookup_product_url(url=url, store_id="1394450", max_price=None, client=swiggy, price_history=None)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
