# Data Model

This document outlines the core domain models and database schema for the Instamart Deal Radar. 
The system uses Pydantic/Dataclasses for in-memory domain models, and SQLite for persistence.

## 1. Domain Models (In-Memory)

The domain layer separates abstract concepts from Instamart-specific JSON.

### 1.1 Products

```python
class CanonicalProduct(BaseModel):
    id: str                  # Internal system ID
    brand: str
    normalized_name: str     # e.g., "nutrabay pure 100 raw whey protein concentrate"
    category: str
    size: str | None
    variant: str | None

class InstamartProduct(BaseModel):
    external_product_id: str # Instamart's item ID
    canonical_product_id: str | None
    name: str                # Display name on Instamart
    url: str
    image_url: str | None
    price: float             # Selling price (normalized to float)
    mrp: float               # Maximum Retail Price
    stock: bool
    category: str
```

### 1.2 Stores and Geography

```python
class Store(BaseModel):
    platform: str            # Always "instamart" for V1
    external_store_id: str   # Instamart's storeId
    name: str | None
    pincode: str | None
    lat: float
    lng: float
    distance_km: float | None
```

### 1.3 Deals and Evaluation

```python
class DealCondition(BaseModel):
    min_discount_pct: float | None
    max_price: float | None
    price_drop_pct: float | None
    require_historical_low: bool = False

class DealEvaluation(BaseModel):
    qualifies: bool
    discount_percent: float
    price: float
    mrp: float
    historical_low: float | None
    trigger_reasons: list[str] # e.g., ["discount_threshold_met", "historical_low"]
```

## 2. SQLite Database Schema (Persistence)

The application utilizes SQLite for caching stores and tracking price histories to power the "Historical Low" feature.

### 2.1 Store Cache (Adapted from CartRadar)

```sql
CREATE TABLE stores (
    id TEXT NOT NULL,
    platform TEXT NOT NULL,
    name TEXT,
    city TEXT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    probe_count INTEGER NOT NULL DEFAULT 1,
    discovered_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (id, platform)
);

CREATE TABLE probed_points (
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    platform TEXT NOT NULL,
    store_id TEXT,
    serviceable INTEGER NOT NULL,
    probed_at TEXT NOT NULL
);
```

### 2.2 Price History (New for Deal Radar)

This tracks price changes over time for specific products at specific stores.

```sql
CREATE TABLE products (
    external_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT
);

CREATE TABLE price_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    price REAL NOT NULL,
    mrp REAL NOT NULL,
    stock INTEGER NOT NULL, -- Boolean 1/0
    
    FOREIGN KEY(product_id) REFERENCES products(external_id)
);
CREATE INDEX idx_price_obs_lookup ON price_observations(product_id, store_id);
CREATE INDEX idx_price_obs_time ON price_observations(timestamp);
```

### 2.3 Alert Rules (Future-proofing)

```sql
CREATE TABLE alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL, -- e.g., Telegram chat ID
    keyword TEXT NOT NULL,
    min_discount REAL,
    max_price REAL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    max_radius_km REAL NOT NULL,
    is_active INTEGER DEFAULT 1
);
```

## 3. SSE Event Schemas

Events streamed from the backend to the frontend React UI.

```python
class SSEEvent(BaseModel):
    type: str # 'search_started', 'location_resolved', 'deal_found', etc.
    data: dict
```

Example `deal_found` data payload:
```json
{
  "product_name": "Nutrabay Pure Whey",
  "price": 2441.0,
  "mrp": 3699.0,
  "discount_pct": 34.0,
  "store": {
    "name": "Store XYZ",
    "distance_km": 3.2
  },
  "triggers": ["Historical Low"],
  "url": "https://www.swiggy.com/instamart/item/12345"
}
```
