import asyncio
from app.api.routers.product_url import lookup_product_url
from app.geo.store_cache import StoreCache
from app.persistence.database import Database
from app.config import get_settings
from app.platforms.blinkit import BlinkitClient

async def test():
    url = "https://blinkit.com/prn/verka-standard-toned-milk/prid/479204"
    try:
        settings = get_settings()
        db = Database(settings.database_path)
        store_cache = StoreCache(db)
        client = BlinkitClient()
        res = await lookup_product_url(url=url, store_id="1394450", max_price=None, client=client, price_history=None)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
