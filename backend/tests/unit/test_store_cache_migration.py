import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from app.geo.store_cache import StoreCache, SCHEMA

def test_fresh_database_has_pincode(tmp_path):
    """TEST 1: Fresh database initialization creates the expected schema including pincode."""
    db_path = tmp_path / "fresh.db"
    cache = StoreCache(db_path)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(stores)")
        columns = [row[1] for row in cursor.fetchall()]
    
    assert "pincode" in columns
    cache.close()

def test_existing_database_migration(tmp_path):
    """TEST 2, 4: Existing database created WITHOUT pincode can be migrated successfully, and records survive."""
    db_path = tmp_path / "legacy.db"
    
    # 1. Manually create the old schema (without pincode)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE stores (
            id TEXT NOT NULL,
            platform TEXT NOT NULL DEFAULT 'zepto',
            name TEXT,
            city TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            probe_count INTEGER NOT NULL DEFAULT 1,
            discovered_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            PRIMARY KEY (id, platform)
        )
        """)
        # Insert a legacy record
        conn.execute("""
        INSERT INTO stores (id, name, city, lat, lng, discovered_at, last_seen_at)
        VALUES ('store1', 'Legacy Store', 'Patna', 25.6, 85.1, '2023-01-01', '2023-01-01')
        """)
        conn.commit()

    # 2. Instantiate StoreCache, which should trigger the migration
    cache = StoreCache(db_path)
    
    # 3. Verify schema
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(stores)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "pincode" in columns
    
    # 4. Verify data survived
    store = cache.get_store('store1', platform='zepto')
    assert store is not None
    assert store.id == 'store1'
    assert store.name == 'Legacy Store'
    assert store.pincode is None  # Survives with NULL/None
    cache.close()

def test_migration_is_idempotent(tmp_path):
    """TEST 3: Migration is idempotent."""
    db_path = tmp_path / "idempotent.db"
    
    # Init first time
    cache1 = StoreCache(db_path)
    cache1.close()
    
    # Init second time
    cache2 = StoreCache(db_path)
    cache2.close()
    
    # Should not throw errors, schema should be intact
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(stores)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "pincode" in columns

def test_upsert_with_pincode(tmp_path):
    """TEST 5: Store upsert with pincode succeeds."""
    db_path = tmp_path / "upsert1.db"
    cache = StoreCache(db_path)
    
    now = datetime.now(timezone.utc).isoformat()
    # Insert new record using the private method, since orchestrator uses it directly or via some proxy
    # Wait, _upsert_store is private. Let's just call it.
    cache._db.execute(
        "INSERT INTO stores (id, platform, name, city, lat, lng, discovered_at, last_seen_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("store2", "zepto", "New Store", "Delhi", 28.6, 77.2, now, now)
    )
    cache._db.commit()
    
    store = cache._upsert_store(28.6, 77.2, "store2", "New Store", "Delhi", now, platform="zepto", pincode="110001")
    assert store.pincode == "110001"
    
    db_store = cache.get_store("store2", "zepto")
    assert db_store.pincode == "110001"
    cache.close()

def test_upsert_without_pincode(tmp_path):
    """TEST 6: Store upsert without pincode remains valid if pincode is optional."""
    db_path = tmp_path / "upsert2.db"
    cache = StoreCache(db_path)
    
    now = datetime.now(timezone.utc).isoformat()
    cache._db.execute(
        "INSERT INTO stores (id, platform, name, city, lat, lng, discovered_at, last_seen_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("store3", "zepto", "Store Without Pincode", "Mumbai", 19.0, 72.8, now, now)
    )
    cache._db.commit()
    
    store = cache._upsert_store(19.0, 72.8, "store3", "Store Without Pincode", "Mumbai", now, platform="zepto")
    assert store.pincode is None
    
    db_store = cache.get_store("store3", "zepto")
    assert db_store.pincode is None
    cache.close()

def test_store_retrieval_returns_pincode(tmp_path):
    """TEST 7: Store retrieval returns pincode correctly."""
    db_path = tmp_path / "retrieve.db"
    cache = StoreCache(db_path)
    now = datetime.now(timezone.utc).isoformat()
    
    cache._db.execute(
        "INSERT INTO stores (id, platform, name, city, pincode, lat, lng, discovered_at, last_seen_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("store4", "instamart", "Another Store", "Bangalore", "560001", 12.9, 77.5, now, now)
    )
    cache._db.commit()
    
    db_store = cache.get_store("store4", "instamart")
    assert db_store.pincode == "560001"
    cache.close()

