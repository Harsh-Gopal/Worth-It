import math
import sqlite3
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path

from app.domain.models.store import Store
from app.geo.haversine import haversine_km, KM_PER_DEG_LAT

SCHEMA = """
CREATE TABLE IF NOT EXISTS stores (
    id TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'instamart',
    name TEXT,
    pincode TEXT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    discovered_at TEXT NOT NULL,
    last_verified_at TEXT NOT NULL,
    PRIMARY KEY (id, platform)
);
"""

class StoreCache:
    def __init__(self, path: Path | str):
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_store(self, store_id: str, platform: str = "instamart") -> Optional[Store]:
        row = self._db.execute(
            "SELECT id, name, pincode, lat, lng, platform FROM stores WHERE id = ? AND platform = ?",
            (store_id, platform)
        ).fetchone()
        if row:
            return Store(
                external_store_id=row[0],
                name=row[1],
                pincode=row[2],
                lat=row[3],
                lng=row[4],
                platform=row[5]
            )
        return None

    def stores_within(self, lat: float, lng: float, radius_km: float, platform: str = "instamart") -> List[Store]:
        """
        Finds stores within an exact radius using an initial bounding box query, 
        followed by precise Haversine filtering.
        """
        dlat = radius_km / KM_PER_DEG_LAT
        # Avoid division by zero at poles, though Instamart is India-only
        dlng = radius_km / (KM_PER_DEG_LAT * max(0.1, math.cos(math.radians(lat))))
        
        rows = self._db.execute(
            "SELECT id, name, pincode, lat, lng, platform FROM stores "
            "WHERE platform = ? AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
            (platform, lat - dlat, lat + dlat, lng - dlng, lng + dlng),
        ).fetchall()
        
        stores = []
        for r in rows:
            dist = haversine_km(lat, lng, r[3], r[4])
            if dist <= radius_km:
                stores.append(Store(
                    external_store_id=r[0],
                    name=r[1],
                    pincode=r[2],
                    lat=r[3],
                    lng=r[4],
                    platform=r[5],
                    distance_km=round(dist, 2)
                ))
        return stores

    def upsert_store(self, store: Store) -> Store:
        """
        Inserts a new store or updates the last_verified_at timestamp.
        Does NOT alter the original coordinates to prevent drift.
        """
        now = self._now()
        existing = self.get_store(store.external_store_id, store.platform)
        
        if existing:
            new_name = store.name or existing.name
            new_pincode = store.pincode or existing.pincode
            self._db.execute(
                "UPDATE stores SET last_verified_at = ?, name = ?, pincode = ? WHERE id = ? AND platform = ?",
                (now, new_name, new_pincode, store.external_store_id, store.platform)
            )
            self._db.commit()
            # Return the canonical stored representation (retaining original lat/lng)
            existing.distance_km = store.distance_km
            existing.name = new_name
            existing.pincode = new_pincode
            return existing
            
        self._db.execute(
            "INSERT INTO stores (id, platform, name, pincode, lat, lng, discovered_at, last_verified_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (store.external_store_id, store.platform, store.name, store.pincode, store.lat, store.lng, now, now)
        )
        self._db.commit()
        return store
