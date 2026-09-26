import asyncio
from app.platforms.flipkart import FlipkartMinutesClient

async def main():
    client = FlipkartMinutesClient()
    lat, lng = 12.9716, 77.5946
    store_id = "test_store_123"
    
    print("Testing Flipkart Minutes Search...")
    products = await client.search("protein", store_id, lat, lng)
    print(f"Found {len(products)} products:")
    for p in products[:10]:
        print(f" - {p.name} (PID: {p.external_product_id}) | Price: {p.price} | MRP: {p.mrp}")
        
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
