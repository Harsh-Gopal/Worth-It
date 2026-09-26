import asyncio
from app.platforms.swiggy import SwiggyClient
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.domain.models.deal import DealCondition
from app.domain.models.alert import AlertRule
from app.geo.store_cache import StoreCache

async def main():
    client = SwiggyClient()
    # 140301 coordinates approximately (using Instamart's default or whatever we have)
    lat, lng = 30.7333, 76.7794 # Chandigarh area coordinates
    
    # Actually wait, let's just use the client's search method directly first
    store_res = await client.resolve_store(lat, lng)
    print(f"Store: {store_res}")
    
    if store_res.store_id:
        print("\n--- Testing search(query='Sports & Fitness') ---")
        products = await client.search("Sports & Fitness", store_res.store_id, lat, lng)
        
        valid_discount = 0
        total = len(products)
        
        for p in products:
            if not p.price or not p.mrp: continue
            if p.mrp <= 0: continue
            
            discount = ((p.mrp - p.price) / p.mrp) * 100
            if discount >= 40:
                valid_discount += 1
                print(f"Found: {p.name} - Price: {p.price}, MRP: {p.mrp}, Discount: {discount:.2f}%")
                
        print(f"\nTotal: {total}, Valid Discount: {valid_discount}")
        
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
