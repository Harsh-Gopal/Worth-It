import re
import os
import logging
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import DictCursor
    from psycopg2 import OperationalError as PgOperationalError, ProgrammingError as PgProgrammingError
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    PgOperationalError = Exception
    PgProgrammingError = Exception

log = logging.getLogger(__name__)

def is_postgres_configured() -> bool:
    return bool(os.getenv("DATABASE_URL") and os.getenv("DATABASE_URL").startswith("postgres"))

def get_postgres_connection():
    if not HAS_PSYCOPG2:
        raise RuntimeError("psycopg2 is not installed but DATABASE_URL is set.")
    url = os.getenv("DATABASE_URL")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(url)
    return PostgresConnectionWrapper(conn)

class RowWrapper:
    def __init__(self, row):
        self._row = row

    def keys(self):
        return list(self._row.keys())

    def __getitem__(self, key):
        return self._row[key]
        
    def __iter__(self):
        return iter(self._row)

class CursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        if cursor:
            self.rowcount = cursor.rowcount
        else:
            self.rowcount = 0

    def fetchone(self):
        if not self.cursor:
            return None
        row = self.cursor.fetchone()
        if row is None:
            return None
        return RowWrapper(row)

    def fetchall(self):
        if not self.cursor:
            return []
        return [RowWrapper(row) for row in self.cursor.fetchall()]

class PostgresConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def _convert_schema_to_pg(self, script: str) -> str:
        s = script
        s = s.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        s = s.replace("BOOLEAN NOT NULL DEFAULT 1", "BOOLEAN NOT NULL DEFAULT TRUE")
        s = s.replace("BOOLEAN NOT NULL DEFAULT 0", "BOOLEAN NOT NULL DEFAULT FALSE")
        return s

    def execute(self, query, params=None):
        pg_query = query.replace("?", "%s")
        
        if "PRAGMA" in pg_query:
            return CursorWrapper(None)

        if "INSERT OR REPLACE INTO alert_rules" in pg_query:
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            pg_query += """ ON CONFLICT (id) DO UPDATE SET 
                name=EXCLUDED.name, categories=EXCLUDED.categories, keywords=EXCLUDED.keywords, 
                exclude_keywords=EXCLUDED.exclude_keywords, product_urls=EXCLUDED.product_urls, 
                pincode=EXCLUDED.pincode, max_price=EXCLUDED.max_price, min_price_drop_pct=EXCLUDED.min_price_drop_pct, 
                require_historical_low=EXCLUDED.require_historical_low, condition_operator=EXCLUDED.condition_operator, 
                require_in_stock=EXCLUDED.require_in_stock, radius_km=EXCLUDED.radius_km, 
                expansion_strategy=EXCLUDED.expansion_strategy, ranking_strategy=EXCLUDED.ranking_strategy, 
                platforms=EXCLUDED.platforms, enabled=EXCLUDED.enabled, created_at=EXCLUDED.created_at, 
                updated_at=EXCLUDED.updated_at, last_run_at=EXCLUDED.last_run_at, cooldown_hours=EXCLUDED.cooldown_hours, 
                lat=EXCLUDED.lat, lng=EXCLUDED.lng, local_store_id=EXCLUDED.local_store_id, 
                telegram_recipient_ids=EXCLUDED.telegram_recipient_ids, run_interval_minutes=EXCLUDED.run_interval_minutes, 
                category_rules=EXCLUDED.category_rules, keyword_rules=EXCLUDED.keyword_rules, exclude_keyword_rules=EXCLUDED.exclude_keyword_rules, product_rules=EXCLUDED.product_rules, 
                min_savings=EXCLUDED.min_savings, adaptive_mode=EXCLUDED.adaptive_mode, pincodes=EXCLUDED.pincodes, search_mode=EXCLUDED.search_mode
            """
        elif "INSERT OR REPLACE INTO app_settings" in pg_query:
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            pg_query += """ ON CONFLICT (key) DO UPDATE SET 
                value_json=EXCLUDED.value_json, updated_at=EXCLUDED.updated_at
            """
        elif "INSERT OR REPLACE INTO alert_events" in pg_query:
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
        elif "INSERT OR REPLACE INTO price_observations" in pg_query:
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            pg_query += """ ON CONFLICT (id) DO UPDATE SET 
                canonical_product_id=EXCLUDED.canonical_product_id, instamart_product_id=EXCLUDED.instamart_product_id, 
                store_id=EXCLUDED.store_id, observed_price=EXCLUDED.observed_price, mrp=EXCLUDED.mrp, 
                discount_percent=EXCLUDED.discount_percent, in_stock=EXCLUDED.in_stock, timestamp=EXCLUDED.timestamp
            """
        elif "INSERT OR REPLACE INTO address_cache" in pg_query:
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            pg_query += """ ON CONFLICT (lat, lng) DO UPDATE SET 
                formatted_address=EXCLUDED.formatted_address, short_address=EXCLUDED.short_address, 
                confidence=EXCLUDED.confidence, provider=EXCLUDED.provider, resolved_at=EXCLUDED.resolved_at
            """
        elif "sqlite_master" in pg_query:
            # Fake support for PRAGMA table_info emulation in StoreCache
            pass

        if "ALTER TABLE" in pg_query:
            pg_query = self._convert_schema_to_pg(pg_query)
            try:
                cursor = self.conn.cursor(cursor_factory=DictCursor)
                cursor.execute(pg_query, params)
                return CursorWrapper(cursor)
            except (PgOperationalError, PgProgrammingError) as e:
                self.conn.rollback()
                if "already exists" in str(e) or "DuplicateColumn" in str(type(e).__name__):
                    return CursorWrapper(None)
                raise e
            
        cursor = self.conn.cursor(cursor_factory=DictCursor)
        
        # In SQLite, "substr(triggered_at, 1, 10)" works, Postgres uses "substring(triggered_at, 1, 10)" or standard.
        pg_query = pg_query.replace("substr(", "substring(")

        if params:
            # Handle int passing to boolean by converting (0,1) into (False, True) for boolean columns
            # Postgres driver might fail if we pass 0/1 to boolean columns.
            # But we don't know the column types. Usually it's fine if we cast in query or if we just let psycopg2 handle it.
            # However, psycopg2 doesn't auto-cast ints to bools. Let's just pass them and see.
            try:
                cursor.execute(pg_query, params)
            except (PgOperationalError, PgProgrammingError) as e:
                self.conn.rollback()
                raise e
        else:
            try:
                cursor.execute(pg_query)
            except (PgOperationalError, PgProgrammingError) as e:
                self.conn.rollback()
                raise e
                
        return CursorWrapper(cursor)

    def commit(self):
        self.conn.commit()

    def executescript(self, script):
        pg_script = self._convert_schema_to_pg(script)
        with self.conn.cursor() as cursor:
            cursor.execute(pg_script)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.conn.rollback()
