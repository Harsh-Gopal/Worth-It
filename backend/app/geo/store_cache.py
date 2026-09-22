"""SQLite cache of discovered dark stores and probed coordinates.

Extended from zepto-finder to support multi-platform stores — each store
row has a `platform` column so we can cache stores per-platform.
"""

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sys
import threading
from typing import Optional

# Cart Radar values
SERVICEABLE_PROBE_TTL_DAYS = 7
UNSERVICEABLE_PROBE_TTL_DAYS = 1

from app.grid import KM_PER_DEG_LAT, haversine_km

_global_store_cache = None

def get_global_cache(path: Path | str) -> 'StoreCache':
    global _global_store_cache
    if _global_store_cache is None:
        _global_store_cache = StoreCache(path)
    return _global_store_cache

SCHEMA = """
CREATE TABLE IF NOT EXISTS stores (
    id TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'zepto',
    name TEXT,
    city TEXT,
    pincode TEXT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    probe_count INTEGER NOT NULL DEFAULT 1,
    discovered_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (id, platform)
);
CREATE TABLE IF NOT EXISTS probed_points (
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    platform TEXT NOT NULL DEFAULT 'zepto',
    store_id TEXT,
    serviceable INTEGER NOT NULL,
    probed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_probed_lat ON probed_points(lat);
CREATE INDEX IF NOT EXISTS idx_probed_platform ON probed_points(platform);
CREATE TABLE IF NOT EXISTS address_cache (
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    formatted_address TEXT NOT NULL,
    short_address TEXT NOT NULL,
    confidence TEXT NOT NULL,
    provider TEXT NOT NULL,
    resolved_at TEXT NOT NULL,
    PRIMARY KEY (lat, lng)
);
"""


@dataclass
class Store:
    """Store as returned by StoreCache queries.

    `external_store_id` is an alias for `id` — the orchestrator uses this
    field name to be consistent with the domain Store model.
    `distance_km` is populated by stores_within() when computing haversine.
    """
    id: str
    name: str | None
    city: str | None
    lat: float
    lng: float
    platform: str = "instamart"
    pincode: str | None = None
    distance_km: float | None = None

    @property
    def external_store_id(self) -> str:
        """Alias for id — compatible with domain Store model."""
        return self.id


class StoreCache:
    def __init__(self, path: Path | str):
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), timeout=30.0, check_same_thread=False)
        self._db.execute("PRAGMA busy_timeout=30000")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)
        self._lock = threading.Lock()

        self._migrate_schema()

        # Heal any coordinates corrupted by the old averaging bug (one-time migration)
        self._heal_corrupted_coordinates()

    def _migrate_schema(self) -> None:
        """Apply idempotent schema migrations for existing databases."""
        with self._lock:
            # Check if pincode column exists in stores table
            cursor = self._db.execute("PRAGMA table_info(stores)")
            columns = [row[1] for row in cursor.fetchall()]
            if "pincode" not in columns:
                self._db.execute("ALTER TABLE stores ADD COLUMN pincode TEXT")
                self._db.commit()

    def _heal_corrupted_coordinates(self) -> None:
        """Fixes store coordinates that were pushed outwards by the old averaging logic.
        Locks every store's position back to the exact point of its first probe."""
        with self._lock:
            stores = self._db.execute("SELECT id, platform, lat, lng FROM stores").fetchall()
            for sid, plat, slat, slng in stores:
                row = self._db.execute(
                    "SELECT lat, lng FROM probed_points WHERE store_id = ? AND platform = ? ORDER BY probed_at ASC LIMIT 1",
                    (sid, plat)
                ).fetchone()
                if row:
                    plat_lat, plat_lng = row
                    if abs(plat_lat - slat) > 0.0001 or abs(plat_lng - slng) > 0.0001:
                        self._db.execute(
                            "UPDATE stores SET lat = ?, lng = ? WHERE id = ? AND platform = ?",
                            (plat_lat, plat_lng, sid, plat)
                        )
            self._db.commit()

    def close(self) -> None:
        if hasattr(self, "_db"):
            self._db.close()

    def get_store(self, store_id: str, platform: str = "instamart") -> Optional[Store]:
        """Fetch a store explicitly by its external ID."""
        with self._lock:
            row = self._db.execute(
                "SELECT id, name, city, lat, lng, platform, pincode FROM stores WHERE id = ?",
                (store_id,)
            ).fetchone()
            if row:
                return Store(id=row[0], name=row[1], city=row[2], lat=row[3], lng=row[4], platform=row[5], pincode=row[6])
            return None

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def stores_within(self, lat: float, lng: float, radius_km: float, platform: str = "instamart") -> list[Store]:
        dlat = radius_km / KM_PER_DEG_LAT
        dlng = radius_km / (KM_PER_DEG_LAT * max(0.1, math.cos(math.radians(lat))))
        rows = self._db.execute(
            "SELECT id, name, city, lat, lng, platform, pincode FROM stores "
            "WHERE platform = ? AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
            (platform, lat - dlat, lat + dlat, lng - dlng, lng + dlng),
        ).fetchall()
        result = []
        for r in rows:
            dist = haversine_km(lat, lng, r[3], r[4])
            if dist <= radius_km:
                # Unpack without distance_km (it's not in DB), set it after construction
                store = Store(id=r[0], name=r[1], city=r[2], lat=r[3], lng=r[4], platform=r[5], pincode=r[6])
                store.distance_km = round(dist, 2)
                result.append(store)
        return result

    def has_fresh_probe_near(self, lat: float, lng: float, within_km: float, platform: str = "zepto") -> bool:
        cutoff_ok = datetime.now(timezone.utc) - timedelta(days=SERVICEABLE_PROBE_TTL_DAYS)
        cutoff_empty = datetime.now(timezone.utc) - timedelta(days=UNSERVICEABLE_PROBE_TTL_DAYS)
        dlat = within_km / KM_PER_DEG_LAT
        dlng = within_km / (KM_PER_DEG_LAT * max(0.1, math.cos(math.radians(lat))))
        rows = self._db.execute(
            "SELECT lat, lng, serviceable, probed_at FROM probed_points "
            "WHERE platform = ? AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
            (platform, lat - dlat, lat + dlat, lng - dlng, lng + dlng),
        ).fetchall()
        for plat, plng, serviceable, probed_at in rows:
            if haversine_km(lat, lng, plat, plng) > within_km:
                continue
            ts = datetime.fromisoformat(probed_at)
            if ts >= (cutoff_ok if serviceable else cutoff_empty):
                return True
        return False

    def _upsert_store(
        self, lat: float, lng: float, store_id: str, store_name: str | None,
        city: str | None, now: str, platform: str = "zepto", pincode: str | None = None
    ) -> Store:
        row = self._db.execute(
            "SELECT lat, lng, probe_count, name, city, pincode FROM stores WHERE id = ? AND platform = ?",
            (store_id, platform),
        ).fetchone()
        if row:
            olat, olng, n, r_name, r_city, r_pincode = row
            # Do NOT average new coordinates into the existing store location.
            # The first-discovered coordinate is authoritative — averaging causes
            # the store to "drift" outwards as the search radius expands, pushing
            # it outside the user's requested radius filter.
            final_name = store_name or r_name
            final_city = city or r_city
            final_pincode = pincode or r_pincode
            self._db.execute(
                "UPDATE stores SET probe_count=?, last_seen_at=?, "
                "name=?, city=?, pincode=? WHERE id=? AND platform=?",
                (n + 1, now, final_name, final_city, final_pincode, store_id, platform),
            )
            return Store(store_id, final_name, final_city, olat, olng, platform, final_pincode)
        self._db.execute(
            "INSERT INTO stores (id, platform, name, city, pincode, lat, lng, probe_count, discovered_at, last_seen_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (store_id, platform, store_name, city, pincode, lat, lng, now, now),
        )
        return Store(store_id, store_name, city, lat, lng, platform, pincode)

    def get_address(self, lat: float, lng: float):
        """Get a cached address for the coordinates."""
        row = self._db.execute(
            "SELECT formatted_address, short_address, confidence, provider FROM address_cache WHERE lat = ? AND lng = ?",
            (lat, lng)
        ).fetchone()
        
        if row:
            from .geocoder import AddressResult
            return AddressResult(
                formatted_address=row[0],
                short_address=row[1],
                confidence=row[2],
                provider=row[3]
            )
        return None

    def save_address(self, lat: float, lng: float, result):
        """Save a resolved address to the cache."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._db:
            self._db.execute(
                """
                INSERT OR REPLACE INTO address_cache 
                (lat, lng, formatted_address, short_address, confidence, provider, resolved_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (lat, lng, result.formatted_address, result.short_address, result.confidence, result.provider, now)
            )

    def record_probe(
        self,
        lat: float,
        lng: float,
        store_id: str | None,
        store_name: str | None = None,
        city: str | None = None,
        platform: str = "zepto",
        pincode: str | None = None,
    ) -> Store | None:
        now = self._now()
        with self._lock:
            self._db.execute(
                "INSERT INTO probed_points (lat, lng, platform, store_id, serviceable, probed_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (lat, lng, platform, store_id, 1 if store_id else 0, now),
            )
            store = self._upsert_store(lat, lng, store_id, store_name, city, now, platform, pincode) if store_id else None
            self._db.commit()
        return store

    def record_store(
        self,
        lat: float,
        lng: float,
        store_id: str | None,
        store_name: str | None = None,
        city: str | None = None,
        platform: str = "zepto",
        pincode: str | None = None,
    ) -> Store | None:
        if not store_id:
            return None
        now = self._now()
        with self._lock:
            store = self._upsert_store(lat, lng, store_id, store_name, city, now, platform, pincode)
            self._db.commit()
        return store

    def stats(self) -> dict:
        stores = self._db.execute("SELECT COUNT(*) FROM stores").fetchone()[0]
        probes = self._db.execute("SELECT COUNT(*) FROM probed_points").fetchone()[0]
        # Per-platform breakdown
        platform_stores = dict(
            self._db.execute("SELECT platform, COUNT(*) FROM stores GROUP BY platform").fetchall()
        )
        return {"stores": stores, "probes": probes, "by_platform": platform_stores}
