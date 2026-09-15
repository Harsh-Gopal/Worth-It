import pytest
from pathlib import Path
from app.geo.store_cache import StoreCache
from app.domain.models.store import Store

@pytest.fixture
def cache(tmp_path: Path):
    db_path = tmp_path / "test_store_cache.db"
    c = StoreCache(db_path)
    yield c
    c.close()

def test_store_cache_upsert_and_get(cache: StoreCache):
    s = Store(external_store_id="123", name="Store 1", lat=12.97, lng=77.59, platform="instamart")
    cache.upsert_store(s)
    
    retrieved = cache.get_store("123")
    assert retrieved is not None
    assert retrieved.name == "Store 1"
    assert retrieved.lat == 12.97

def test_store_cache_upsert_deduplication(cache: StoreCache):
    s1 = Store(external_store_id="123", name="Store 1", lat=12.97, lng=77.59, platform="instamart")
    cache.upsert_store(s1)
    
    # Simulate a second probe discovering the same store slightly offset
    s2 = Store(external_store_id="123", name="Store 1 Updated", lat=12.98, lng=77.60, platform="instamart")
    updated = cache.upsert_store(s2)
    
    # Original coordinates must be preserved (no drift)
    assert updated.lat == 12.97
    assert updated.lng == 77.59
    assert updated.name == "Store 1 Updated"
    
    # Should only be one row
    assert len(cache.stores_within(12.97, 77.59, 10.0)) == 1

def test_store_cache_stores_within_exact_radius(cache: StoreCache):
    # Insert a store exactly 5.8 km away (e.g. lat + 0.052 degree approx)
    # Center: 12.97, 77.59
    s = Store(external_store_id="999", name="Border Store", lat=12.97 + 0.052, lng=77.59, platform="instamart")
    cache.upsert_store(s)
    
    # 5.0 km radius MUST NOT include this store
    stores_5km = cache.stores_within(12.97, 77.59, 5.0)
    assert len(stores_5km) == 0
    
    # 6.0 km radius MUST include this store
    stores_6km = cache.stores_within(12.97, 77.59, 6.0)
    assert len(stores_6km) == 1
    assert stores_6km[0].distance_km > 5.0
