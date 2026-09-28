pg_query = """INSERT OR REPLACE INTO alert_events (
    id, alert_rule_id, canonical_product_id, instamart_product_id,
    product_name, product_url, store_id, store_name, distance_km,
    price, mrp, discount_percent, previous_price, price_drop_percent,
    trigger_reason, triggered_at, notification_status, notification_attempts,
    product_image, platform, store_pincode, search_pincode, origin_lat, origin_lng,
    deal_level, deal_score, savings_amount, applicable_rule, scan_run_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

if "INSERT OR REPLACE INTO alert_events" in pg_query:
    pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO")
    pg_query += """ ON CONFLICT (id) DO UPDATE SET 
        alert_rule_id=EXCLUDED.alert_rule_id, canonical_product_id=EXCLUDED.canonical_product_id, 
        instamart_product_id=EXCLUDED.instamart_product_id, product_name=EXCLUDED.product_name, 
        product_url=EXCLUDED.product_url, store_id=EXCLUDED.store_id, store_name=EXCLUDED.store_name, 
        distance_km=EXCLUDED.distance_km, price=EXCLUDED.price, mrp=EXCLUDED.mrp, 
        discount_percent=EXCLUDED.discount_percent, previous_price=EXCLUDED.previous_price, 
        price_drop_percent=EXCLUDED.price_drop_percent, trigger_reason=EXCLUDED.trigger_reason, 
        triggered_at=EXCLUDED.triggered_at, notification_status=EXCLUDED.notification_status, 
        notification_attempts=EXCLUDED.notification_attempts, product_image=EXCLUDED.product_image, 
        platform=EXCLUDED.platform, store_pincode=EXCLUDED.store_pincode, search_pincode=EXCLUDED.search_pincode, 
        origin_lat=EXCLUDED.origin_lat, origin_lng=EXCLUDED.origin_lng, deal_level=EXCLUDED.deal_level, 
        deal_score=EXCLUDED.deal_score, savings_amount=EXCLUDED.savings_amount, 
        applicable_rule=EXCLUDED.applicable_rule, scan_run_id=EXCLUDED.scan_run_id
    """
    
print(pg_query)
