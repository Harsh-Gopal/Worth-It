from typing import List, Optional, Tuple
import uuid
from datetime import datetime, timezone
import sqlite3

from app.domain.models.price_observation import PriceObservation
from app.persistence.database import Database

class PriceHistoryRepository:
    def __init__(self, db: Database):
        self.db = db

    def record_observation(self, obs: PriceObservation) -> PriceObservation:
        if not obs.id:
            obs.id = str(uuid.uuid4())
            
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO price_observations (
                    id, canonical_product_id, instamart_product_id, store_id, 
                    observed_price, mrp, discount_percent, in_stock, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    obs.id, obs.canonical_product_id, obs.instamart_product_id, obs.store_id,
                    obs.observed_price, obs.mrp, obs.discount_percent, obs.in_stock, 
                    obs.timestamp.isoformat()
                )
            )
            conn.commit()
        return obs

    def get_latest_observation(self, instamart_product_id: str, store_id: str) -> Optional[PriceObservation]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM price_observations 
                WHERE instamart_product_id = ? AND store_id = ? 
                ORDER BY timestamp DESC LIMIT 1
                """,
                (instamart_product_id, store_id)
            ).fetchone()
            
            if row:
                return self._row_to_obs(row)
        return None

    def get_previous_observation(self, instamart_product_id: str, store_id: str, before_timestamp: datetime) -> Optional[PriceObservation]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM price_observations 
                WHERE instamart_product_id = ? AND store_id = ? AND timestamp < ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (instamart_product_id, store_id, before_timestamp.isoformat())
            ).fetchone()
            
            if row:
                return self._row_to_obs(row)
        return None

    def get_historical_low(self, instamart_product_id: str, store_id: str, before_timestamp: Optional[datetime] = None) -> Optional[float]:
        query = "SELECT MIN(observed_price) as min_price FROM price_observations WHERE instamart_product_id = ? AND store_id = ?"
        params = [instamart_product_id, store_id]
        
        if before_timestamp:
            query += " AND timestamp < ?"
            params.append(before_timestamp.isoformat())
            
        with self.db.get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            if row and row["min_price"] is not None:
                return float(row["min_price"])
        return None

    def _row_to_obs(self, row: sqlite3.Row) -> PriceObservation:
        return PriceObservation(
            id=row["id"],
            canonical_product_id=row["canonical_product_id"],
            instamart_product_id=row["instamart_product_id"],
            store_id=row["store_id"],
            observed_price=row["observed_price"],
            mrp=row["mrp"],
            discount_percent=row["discount_percent"],
            in_stock=bool(row["in_stock"]),
            timestamp=datetime.fromisoformat(row["timestamp"])
        )
