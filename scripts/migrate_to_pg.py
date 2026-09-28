import os
import sys
import json
import sqlite3
from pathlib import Path

# Add backend to sys.path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.persistence.database import Database
from app.geo.store_cache import StoreCache, get_global_cache
from app.persistence.pg_wrapper import is_postgres_configured, get_postgres_connection

def migrate():
    if not is_postgres_configured():
        print("PostgreSQL is not configured. Set DATABASE_URL.")
        return

    settings = get_settings()
    
    sqlite_db_path = settings.database_path
    if not sqlite_db_path.exists():
        print(f"No SQLite database found at {sqlite_db_path}. Nothing to migrate.")
        return

    print("Migrating data to PostgreSQL...")

    sqlite_conn = sqlite3.connect(str(sqlite_db_path))
    sqlite_conn.row_factory = sqlite3.Row
    
    pg_db = Database(sqlite_db_path)
    
    # 1. Migrate app_settings
    settings_file = settings.data_dir / "user_settings.json"
    if settings_file.exists():
        print("Migrating user_settings.json to app_settings...")
        try:
            data = json.loads(settings_file.read_text())
            from app.persistence.repositories.settings_repo import SettingsRepository
            repo = SettingsRepository(pg_db)
            repo.save_user_settings(data)
        except Exception as e:
            print(f"Error migrating user_settings.json: {e}")
            
    # 2. Migrate alert_rules
    print("Migrating alert_rules...")
    rules = sqlite_conn.execute("SELECT * FROM alert_rules").fetchall()
    with pg_db.get_connection() as pg_conn:
        for rule in rules:
            cols = list(rule.keys())
            vals = [rule[c] for c in cols]
            placeholders = ", ".join(["%s"] * len(cols))
            
            # Use ON CONFLICT DO NOTHING to avoid duplicates if rerun
            query = f"INSERT INTO alert_rules ({', '.join(cols)}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
            try:
                pg_conn.execute(query, tuple(vals))
            except Exception as e:
                print(f"Error migrating rule {rule['id']}: {e}")
                
    # 3. Migrate alert_events
    print("Migrating alert_events...")
    events = sqlite_conn.execute("SELECT * FROM alert_events").fetchall()
    with pg_db.get_connection() as pg_conn:
        for event in events:
            cols = list(event.keys())
            vals = [event[c] for c in cols]
            placeholders = ", ".join(["%s"] * len(cols))
            
            query = f"INSERT INTO alert_events ({', '.join(cols)}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
            try:
                pg_conn.execute(query, tuple(vals))
            except Exception as e:
                print(f"Error migrating event {event['id']}: {e}")
                
    # 4. Migrate price_observations
    print("Migrating price_observations...")
    obs = sqlite_conn.execute("SELECT * FROM price_observations").fetchall()
    with pg_db.get_connection() as pg_conn:
        for o in obs:
            cols = list(o.keys())
            vals = [o[c] for c in cols]
            placeholders = ", ".join(["%s"] * len(cols))
            
            query = f"INSERT INTO price_observations ({', '.join(cols)}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
            try:
                pg_conn.execute(query, tuple(vals))
            except Exception as e:
                print(f"Error migrating observation {o['id']}: {e}")
                
    # 5. Migrate stores cache
    sqlite_stores_path = settings.store_cache_path
    if sqlite_stores_path.exists():
        print("Migrating stores cache...")
        stores_conn = sqlite3.connect(str(sqlite_stores_path))
        stores_conn.row_factory = sqlite3.Row
        
        pg_store_cache = StoreCache(sqlite_stores_path)
        
        # Migrate address_cache
        addrs = stores_conn.execute("SELECT * FROM address_cache").fetchall()
        with pg_store_cache._db as pg_conn:
            for addr in addrs:
                cols = list(addr.keys())
                vals = [addr[c] for c in cols]
                placeholders = ", ".join(["%s"] * len(cols))
                
                query = f"INSERT INTO address_cache ({', '.join(cols)}) VALUES ({placeholders}) ON CONFLICT (lat, lng) DO NOTHING"
                try:
                    pg_conn.execute(query, tuple(vals))
                except Exception as e:
                    print(f"Error migrating address {addr['lat']},{addr['lng']}: {e}")
                    
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
