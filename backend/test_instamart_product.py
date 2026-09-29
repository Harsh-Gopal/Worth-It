import asyncio
import logging
from app.platforms.swiggy import SwiggyClient
from app.core.browser import BrowserManager

logging.basicConfig(level=logging.INFO)

async def main():
    client = SwiggyClient()
    lat, lng = 28.5355, 77.3910 # random location
    store = await client.resolve_store(lat, lng)
    if store and store.serviceable:
        # A known product ID from Instamart. I'll search first to get one.
        results = await client.search("milk", store.store_id, lat, lng)
        if not results:
            print("No search results")
            return
        first_product = results[0]
        print(f"Testing product_at_store for: {first_product}")
        product_id = getattr(first_product, 'product_id', getattr(first_product, 'id', getattr(first_product, 'external_product_id', None)))
        print(f"Found product_id: {product_id}")
        if product_id:
            result = await client.product_at_store(product_id, store.store_id, lat, lng)
            print(f"Result: {result}")
        print(f"Result: {result}")

    await BrowserManager.close()

if __name__ == "__main__":
    asyncio.run(main())
