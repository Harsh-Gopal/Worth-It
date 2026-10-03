import asyncio
import sys
import logging
from app.platforms.flipkart_minutes import FlipkartMinutesClient
from app.platforms.swiggy import SwiggyClient
from app.api.routers.location import nom_forward
from app.platforms.promo_price import _parse_item_page
from app.links import extract_canonical_url

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("verify")

async def test_location_autocomplete():
    log.info("Testing location autocomplete (Swiggy + FM)")
    from app.api.routers.location import suggest_locations, resolve_location_get
    
    # 1. Test suggest
    res = await suggest_locations("800014")
    assert "suggestions" in res
    assert len(res["suggestions"]) > 0
    
    # 2. Test resolve
    res_loc = await resolve_location_get("800014")
    log.info(f"Resolved Location: {res_loc}")
    assert res_loc.lat is not None
    assert res_loc.lng is not None
    assert res_loc.local_store_id is not None
    assert res_loc.fm_store_id is not None
    return res_loc.lat, res_loc.lng

async def test_wishlist_extraction():
    log.info("Testing wishlist extraction with extra text")
    text = "Check out this product on Zepto! https://www.zeptonow.com/pn/daawat-rozana-super-basmati-rice-medium-grain/pvid/78514101-7292-4f01-b3b0-642159fa658e?query=rice"
    platform, canonical, err = extract_canonical_url(text)
    log.info(f"Extracted: platform={platform}, url={canonical}")
    assert platform == "zepto"

    text2 = "Here is instamart https://instamart.in/item/917UXELNGA?share=true check it out"
    platform2, canonical2, err2 = extract_canonical_url(text2)
    log.info(f"Extracted: platform={platform2}, url={canonical2}")
    assert platform2 == "swiggy"

async def test_instamart_flash_price():
    log.info("Testing Instamart Flash Price for 917UXELNGA")
    # https://instamart.in/item/917UXELNGA?share=true
    # https://instamart.in/item/NRRQJ4R2XW?share=true
    
    from app.platforms.promo_price import fetch_flash_price
    lat, lng = 12.9716, 77.5946
    
    res1 = await fetch_flash_price("917UXELNGA", lat, lng)
    log.info(f"Flash Price 1: {res1}")
    
    res2 = await fetch_flash_price("NRRQJ4R2XW", lat, lng)
    log.info(f"Flash Price 2: {res2}")

async def test_flipkart_minutes_api():
    log.info("Testing Flipkart Minutes API flow")
    fm = FlipkartMinutesClient()
    # Resolve store for 800014
    # Patna coordinates roughly
    lat = 25.5941
    lng = 85.1376
    store_res = await fm.resolve_store(lat, lng)
    log.info(f"FM Store Res: {store_res}")
    
    if store_res and store_res.serviceable:
        # Test search
        search_res = await fm.search("milk", store_res.store_id, lat=lat, lng=lng)
        log.info(f"FM Search found {len(search_res)} items")

async def main():
    await test_wishlist_extraction()
    await test_location_autocomplete()
    await test_instamart_flash_price()
    await test_flipkart_minutes_api()
    log.info("All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
