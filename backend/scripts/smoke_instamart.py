import os
import sys
import asyncio
import time
from typing import List, Dict, Any

from app.core.config import settings
from app.platforms.instamart.session import BrowserClient
from app.platforms.instamart.client import geocode, select_store
from app.domain.models.deal import DealCondition
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.geo.store_cache import StoreCache

async def run_smoke_test():
    print("=== LIVE INSTAMART GEOGRAPHIC SMOKE TEST ===")
    
    # Configuration
    keyword = os.getenv("TEST_KEYWORD", "nutrabay protein")
    test_area = os.getenv("TEST_AREA", "Bandra, Mumbai")
    db_path = os.getenv("TEST_DB_PATH", "smoke_cache.db")
    
    print(f"Test Area: {test_area}")
    print(f"Test Keyword: {keyword}")
    print(f"Cache DB: {db_path}\n")
    
    start_time = time.time()
    metrics = {
        "local_search_duration": 0,
        "probes": 0,
        "unique_stores": 0,
        "targeted_checks": 0,
        "qualifying_deals": 0
    }

    print("1. Bootstrapping WAF Session (Playwright)...")
    try:
        browser_client = BrowserClient(
            proxy_url=settings.proxy,
            headless=settings.headless,
            block_images=settings.block_images,
            profile=settings.browser_profile,
            data_dir=settings.data_dir,
            timeout_sec=settings.bootstrap_seconds
        )
        browser_client.start()
        client = browser_client.build_client()
        browser_client.close()
        print("✓ SESSION")
    except Exception as e:
        print(f"✗ SESSION: {e}")
        sys.exit(1)

    print("\n2. Geocoding & Resolving Local Store...")
    try:
        place = geocode(client, test_area)
        center_lat, center_lng = place['lat'], place['lng']
        print(f"✓ LOCATION: {place['title']} ({center_lat}, {center_lng})")
        local_store_id = select_store(client, place)
        print(f"✓ STORE: {local_store_id}")
    except Exception as e:
        print(f"✗ LOCATION/STORE: {e}")
        sys.exit(1)

    print(f"\n3. Running Geographic Deal Search Orchestrator for '{keyword}'...")
    store_cache = StoreCache(db_path)
    orchestrator = DealSearchOrchestrator(
        client=client, 
        store_cache=store_cache,
        center_lat=center_lat, 
        center_lng=center_lng,
        local_store_id=local_store_id
    )

    # Search for anything >= 10% discount just to see hits
    condition = DealCondition(min_discount_pct=10.0)
    
    local_start = 0
    try:
        async for event in orchestrator.run_search(
            search_id="smoke_123", 
            keyword=keyword, 
            condition=condition, 
            expansion_radii_km=[3.0, 5.0],  # Keep smoke test tight to avoid hammering
            strategy="NEARBY_FIRST"
        ):
            etype = event["event"]
            data = event["data"]
            
            if etype == "local_search_started":
                local_start = time.time()
            elif etype == "local_search_completed":
                metrics["local_search_duration"] = round(time.time() - local_start, 2)
            elif etype == "probe_started":
                metrics["probes"] += data["count"]
            elif etype == "store_discovered":
                metrics["unique_stores"] += 1
            elif etype == "product_check_started":
                metrics["targeted_checks"] += data["count"]
            elif etype == "deal_found":
                metrics["qualifying_deals"] += 1
                print(f"  [!] DEAL: {data['product_name']} | ₹{data['price']} (MRP ₹{data['mrp']}) | {data['discount_pct']}% off | Store: {data['store_id']}")
            elif etype in ("search_error", "store_scan_failed", "product_check_failed"):
                print(f"  [✗] {etype.upper()}: {data}")
            elif etype in ("radius_scan_started", "search_completed"):
                print(f"  > {etype}: {data}")
                
        print("✓ ORCHESTRATOR SEARCH")
    except Exception as e:
        print(f"✗ SEARCH FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    store_cache.close()
    
    total_duration = round(time.time() - start_time, 2)
    
    print("\n============================================================")
    print("                      SEARCH SUMMARY                        ")
    print("============================================================")
    print(f"Keyword:                 {keyword}")
    print(f"Local store:             {local_store_id}")
    print(f"Radius:                  5.0 km (Max)")
    print(f"Probes:                  {metrics['probes']}")
    print(f"Unique stores found:     {metrics['unique_stores']}")
    print(f"Targeted product checks: {metrics['targeted_checks']}")
    print(f"Qualifying deals:        {metrics['qualifying_deals']}")
    print(f"Browser launches:        1")
    print(f"Local search duration:   {metrics['local_search_duration']} seconds")
    print(f"Total duration:          {total_duration} seconds")
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
