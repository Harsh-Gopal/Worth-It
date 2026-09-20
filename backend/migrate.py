from app.config import get_settings
import sqlite3

settings = get_settings()
conn = sqlite3.connect(settings.database_path)
cur = conn.cursor()

columns_to_add = [
    ("keywords", "TEXT NOT NULL DEFAULT '[]'"),
    ("exclude_keywords", "TEXT NOT NULL DEFAULT '[]'"),
    ("categories", "TEXT NOT NULL DEFAULT '[]'"),
    ("product_urls", "TEXT NOT NULL DEFAULT '[]'"),
    ("name", "TEXT NOT NULL DEFAULT ''"),
    ("min_discount_pct", "REAL"),
    ("max_price", "REAL"),
    ("min_price_drop_pct", "REAL"),
    ("require_historical_low", "BOOLEAN NOT NULL DEFAULT 0"),
    ("condition_operator", "TEXT NOT NULL DEFAULT 'AND'"),
    ("require_in_stock", "BOOLEAN NOT NULL DEFAULT 1"),
    ("radius_km", "REAL NOT NULL DEFAULT 10.0"),
    ("expansion_strategy", "TEXT NOT NULL DEFAULT 'NEARBY_FIRST'"),
    ("ranking_strategy", "TEXT NOT NULL DEFAULT 'BEST_DISCOUNT'"),
    ("platform", "TEXT NOT NULL DEFAULT 'instamart'"),
    ("enabled", "BOOLEAN NOT NULL DEFAULT 1"),
    ("cooldown_hours", "REAL NOT NULL DEFAULT 24.0"),
    ("lat", "REAL"),
    ("lng", "REAL"),
    ("local_store_id", "TEXT"),
    ("telegram_recipient_ids", "TEXT NOT NULL DEFAULT '[]'"),
    ("run_interval_minutes", "INTEGER NOT NULL DEFAULT 0")
]

cur.execute("PRAGMA table_info(alert_rules)")
existing_cols = {row[1] for row in cur.fetchall()}

for col_name, col_def in columns_to_add:
    if col_name not in existing_cols:
        try:
            cur.execute(f"ALTER TABLE alert_rules ADD COLUMN {col_name} {col_def}")
            print(f"Added column {col_name}")
        except Exception as e:
            print(f"Failed to add {col_name}: {e}")

conn.commit()
print("Migration completed.")
