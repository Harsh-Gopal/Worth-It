"""Tests for geo/store_cache.StoreCache.

Adapted to use the actual available API:
  - _upsert_store() (private, used internally by orchestrator)
  - stores_within()
  - record_store() (public convenience wrapper)
"""

import pytest
from pathlib import Path
from app.geo.store_cache import StoreCache, Store


@pytest.fixture
def cache(tmp_path: Path):
    db_path = tmp_path / "test_store_cache.db"
    c = StoreCache(db_path)
    yield c
    c.close()


def _insert(cache: StoreCache, store_id: str, name: str, lat: float, lng: float) -> Store:
    """Helper: upsert a store using the internal method (as the orchestrator does)."""
    return cache._upsert_store(
        lat, lng, store_id, name, None, cache._now(), "instamart"
    )


def test_store_cache_upsert_and_find(cache: StoreCache):
    _insert(cache, "store-123", "Test Store", lat=12.97, lng=77.59)

    stores = cache.stores_within(12.97, 77.59, 1.0, "instamart")
    assert len(stores) == 1
    assert stores[0].id == "store-123"
    assert stores[0].name == "Test Store"
    assert stores[0].lat == pytest.approx(12.97, abs=0.001)


def test_store_cache_upsert_deduplication(cache: StoreCache):
    _insert(cache, "store-123", "Store 1", lat=12.97, lng=77.59)
    # Second probe same store — coordinates must not drift
    updated = _insert(cache, "store-123", "Store 1 Updated", lat=12.98, lng=77.60)

    # Coordinates should be preserved from first insert (no drift from averaging)
    assert updated.lat == pytest.approx(12.97, abs=0.01)
    assert updated.lng == pytest.approx(77.59, abs=0.01)
    assert updated.name == "Store 1 Updated"

    # Should only be one row
    stores = cache.stores_within(12.97, 77.59, 10.0, "instamart")
    assert len(stores) == 1


def test_store_cache_stores_within_exact_radius(cache: StoreCache):
    # Store ~5.8 km away (lat + 0.052 deg ≈ 5.8 km at equator)
    _insert(cache, "far-store", "Border Store", lat=12.97 + 0.052, lng=77.59)

    # 5.0 km radius MUST NOT include this store
    stores_5km = cache.stores_within(12.97, 77.59, 5.0, "instamart")
    assert len(stores_5km) == 0

    # 6.0 km radius MUST include this store
    stores_6km = cache.stores_within(12.97, 77.59, 6.0, "instamart")
    assert len(stores_6km) == 1
