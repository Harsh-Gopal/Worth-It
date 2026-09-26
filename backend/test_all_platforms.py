import asyncio
from app.platforms.swiggy import SwiggyClient
from app.platforms.zepto.client import ZeptoClient
from app.platforms.blinkit import BlinkitClient
from app.platforms.flipkart import FlipkartMinutesClient

async def test_platform(client, lat, lng, query="Sports & Fitness"):
    print(f"\n================ {client.display_name} ================")
    try:
        store_res = await client.resolve_store(lat, lng)
        print(f"Store: {store_res.store_name} ({store_res.store_id})")
        if store_res.store_id:
            products = await client.search(query, store_res.store_id, lat, lng)
            
            valid_discount = 0
            for p in products:
                if not p.price or not p.mrp: continue
                if p.mrp <= 0: continue
                
                discount = ((p.mrp - p.price) / p.mrp) * 100
                if discount >= 40:
                    valid_discount += 1
                    print(f"Found: {p.name} - Price: {p.price}, MRP: {p.mrp}, Discount: {discount:.2f}%")
            print(f"Total: {len(products)}, Valid Discount: {valid_discount}")
    except Exception as e:
        print(f"Error testing {client.display_name}: {e}")
    finally:
        await client.aclose()

async def main():
    # 140301 (Chandigarh / Mohali side approx lat/lng)
    lat_140301, lng_140301 = 30.7333, 76.7794 
    # 800014 (Patna approx lat/lng)
    lat_800014, lng_800014 = 25.5941, 85.1376 
    
    await test_platform(SwiggyClient(), lat_140301, lng_140301)
    await test_platform(ZeptoClient(), lat_140301, lng_140301)
    await test_platform(BlinkitClient(), lat_140301, lng_140301)
    await test_platform(FlipkartMinutesClient(), lat_800014, lng_800014)

if __name__ == "__main__":
    asyncio.run(main())
