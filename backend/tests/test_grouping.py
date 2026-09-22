import pytest
from datetime import datetime, timezone, timedelta
from app.domain.models.alert import AlertEvent
from app.domain.services.grouping_service import ProductGroupingService

def utc_now():
    return datetime.now(timezone.utc)

def test_grouping_service_basic():
    now = utc_now()
    # 9:00 AM UTC
    now = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    e1 = AlertEvent(
        id="1", alert_rule_id="r1", instamart_product_id="P1", product_name="Elvan Chocolate",
        platform="instamart", store_id="S1", price=99.0, mrp=349.0, discount_percent=71.6,
        trigger_reason="Best price", triggered_at=now, store_pincode="800001",
        distance_km=1.0, product_url="url1"
    )
    e2 = AlertEvent(
        id="2", alert_rule_id="r1", instamart_product_id="P1", product_name="Elvan Chocolate",
        platform="instamart", store_id="S2", price=109.0, mrp=349.0, discount_percent=68.7,
        trigger_reason="Good deal", triggered_at=now + timedelta(hours=2), store_pincode="800002",
        distance_km=2.0, product_url="url2"
    )
    # Different product
    e4 = AlertEvent(
        id="4", alert_rule_id="r1", instamart_product_id="P2", product_name="Milk",
        platform="instamart", store_id="S1", price=50.0, mrp=55.0, discount_percent=9.0,
        trigger_reason="Milk deal", triggered_at=now + timedelta(hours=1), store_pincode="800001",
        distance_km=1.0, product_url="url4"
    )

    events = [e1, e2, e4]
    # Use UTC for offset to simplify tests (tz_offset_mins=0)
    grouped = ProductGroupingService.group_events(events, tz_offset_mins=0)
    
    assert len(grouped) == 2
    
    # Chocolate group
    choc = next(g for g in grouped if g.instamart_product_id == "P1")
    assert choc.locations_count == 2
    assert choc.best_price == 99.0
    assert choc.best_discount_percent == 71.6
    assert choc.trigger_reason == "Best price"
    assert len(choc.offers) == 2
    # Local date should match the UTC date since offset is 0
    assert choc.local_date == now.strftime('%Y-%m-%d')
    
    # Milk group
    milk = next(g for g in grouped if g.instamart_product_id == "P2")
    assert milk.locations_count == 1
    assert milk.best_price == 50.0

def test_grouping_service_same_store_dedup():
    now = utc_now()
    # If the exact same store has the exact same price multiple times in the day
    e1 = AlertEvent(
        id="1", alert_rule_id="r1", instamart_product_id="P1", product_name="Elvan Chocolate",
        platform="instamart", store_id="S1", price=99.0, mrp=349.0, discount_percent=71.6,
        trigger_reason="Best price", triggered_at=now
    )
    e2 = AlertEvent(
        id="2", alert_rule_id="r1", instamart_product_id="P1", product_name="Elvan Chocolate",
        platform="instamart", store_id="S1", price=99.0, mrp=349.0, discount_percent=71.6,
        trigger_reason="Better price", triggered_at=now + timedelta(hours=2)
    )
    # Price changed meaningfully!
    e3 = AlertEvent(
        id="3", alert_rule_id="r1", instamart_product_id="P1", product_name="Elvan Chocolate",
        platform="instamart", store_id="S1", price=120.0, mrp=349.0, discount_percent=60.0,
        trigger_reason="Price drop", triggered_at=now - timedelta(hours=1)
    )

    grouped = ProductGroupingService.group_events([e1, e2, e3], tz_offset_mins=0)
    assert len(grouped) == 1
    g = grouped[0]
    
    # e1 and e2 should be deduplicated (keep latest = e2). e3 kept because price is different.
    assert g.locations_count == 2
    prices = [o.price for o in g.offers]
    assert 99.0 in prices
    assert 120.0 in prices

