import sqlite3
from pathlib import Path

SCHEMA = """
-- Core Price Observations
CREATE TABLE IF NOT EXISTS price_observations (
    id TEXT PRIMARY KEY,
    canonical_product_id TEXT,
    instamart_product_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    observed_price REAL NOT NULL,
    mrp REAL NOT NULL,
    discount_percent REAL NOT NULL,
    in_stock BOOLEAN NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_obs_product_store ON price_observations(instamart_product_id, store_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_obs_canonical ON price_observations(canonical_product_id, timestamp DESC);

-- Alert Rules
CREATE TABLE IF NOT EXISTS alert_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    categories TEXT NOT NULL DEFAULT '[]',
    keywords TEXT NOT NULL DEFAULT '[]',
    exclude_keywords TEXT NOT NULL DEFAULT '[]',
    product_urls TEXT NOT NULL DEFAULT '[]',
    min_discount_pct REAL,
    max_price REAL,
    min_price_drop_pct REAL,
    require_historical_low BOOLEAN NOT NULL DEFAULT 0,
    condition_operator TEXT NOT NULL DEFAULT 'AND',
    require_in_stock BOOLEAN NOT NULL DEFAULT 1,
    radius_km REAL NOT NULL DEFAULT 10.0,
    expansion_strategy TEXT NOT NULL DEFAULT 'NEARBY_FIRST',
    ranking_strategy TEXT NOT NULL DEFAULT 'BEST_DISCOUNT',
    platform TEXT NOT NULL DEFAULT 'instamart',
    enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    cooldown_hours REAL NOT NULL DEFAULT 24.0,
    lat REAL,
    lng REAL,
    local_store_id TEXT,
    telegram_recipient_ids TEXT NOT NULL DEFAULT '[]',
    run_interval_minutes INTEGER NOT NULL DEFAULT 0
);

-- Alert Events (Triggered Deals)
CREATE TABLE IF NOT EXISTS alert_events (
    id TEXT PRIMARY KEY,
    alert_rule_id TEXT NOT NULL,
    canonical_product_id TEXT,
    instamart_product_id TEXT NOT NULL,
    product_name TEXT NOT NULL DEFAULT '',
    product_url TEXT,
    store_id TEXT NOT NULL,
    store_name TEXT,
    distance_km REAL,
    price REAL NOT NULL,
    mrp REAL NOT NULL,
    discount_percent REAL NOT NULL,
    previous_price REAL,
    price_drop_percent REAL,
    trigger_reason TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    notification_status TEXT NOT NULL DEFAULT 'pending',
    notification_attempts INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(alert_rule_id) REFERENCES alert_rules(id)
);

CREATE INDEX IF NOT EXISTS idx_events_rule ON alert_events(alert_rule_id, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_product_store ON alert_events(instamart_product_id, store_id, triggered_at DESC);

-- Notification Results
CREATE TABLE IF NOT EXISTS notification_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_event_id TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    provider TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    error_message TEXT,
    retryable BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY(alert_event_id) REFERENCES alert_events(id)
);
"""

# Incremental migrations — add new columns to existing databases
_MIGRATIONS = [
    # alert_rules new columns
    "ALTER TABLE alert_rules ADD COLUMN name TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE alert_rules ADD COLUMN categories TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE alert_rules ADD COLUMN exclude_keywords TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE alert_rules ADD COLUMN product_urls TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE alert_rules ADD COLUMN telegram_recipient_ids TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE alert_rules ADD COLUMN run_interval_minutes INTEGER NOT NULL DEFAULT 0",
    # alert_events new columns
    "ALTER TABLE alert_events ADD COLUMN product_name TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE alert_events ADD COLUMN product_url TEXT",
    "ALTER TABLE alert_events ADD COLUMN store_name TEXT",
    "ALTER TABLE alert_events ADD COLUMN distance_km REAL",
    "ALTER TABLE alert_events ADD COLUMN product_image TEXT",
    "ALTER TABLE alert_events ADD COLUMN platform TEXT NOT NULL DEFAULT 'instamart'",
    "ALTER TABLE alert_events ADD COLUMN store_pincode TEXT",
    "ALTER TABLE alert_events ADD COLUMN search_pincode TEXT",
    "ALTER TABLE alert_events ADD COLUMN origin_lat REAL",
    "ALTER TABLE alert_events ADD COLUMN origin_lng REAL",
]


class Database:
    def __init__(self, path: "Path | str"):
        if isinstance(path, str):
            path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._init_db()

    def _init_db(self):
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)
            for sql in _MIGRATIONS:
                try:
                    conn.execute(sql)
                    conn.commit()
                except sqlite3.OperationalError:
                    pass  # Column already exists

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
