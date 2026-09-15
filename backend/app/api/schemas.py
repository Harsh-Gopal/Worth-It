from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Search Schemas ───────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    categories: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    exclude_keywords: List[str] = Field(default_factory=list)
    product_urls: List[str] = Field(default_factory=list)  # Exact Instamart URLs (wishlist mode)
    min_discount_pct: Optional[float] = None
    max_price: Optional[float] = None
    min_price_drop_pct: Optional[float] = None
    require_historical_low: bool = False
    condition_operator: str = "AND"
    require_in_stock: bool = True
    radius_km: float = Field(10.0, le=20.0, description="Max 20km enforced server-side")
    expansion_strategy: str = "NEARBY_FIRST"
    lat: Optional[float] = None
    lng: Optional[float] = None
    local_store_id: Optional[str] = None


# ─── Alert Schemas ────────────────────────────────────────────────────────────

class AlertRuleCreate(BaseModel):
    name: str = ""
    categories: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    exclude_keywords: List[str] = Field(default_factory=list)
    product_urls: List[str] = Field(default_factory=list)
    min_discount_pct: Optional[float] = None
    max_price: Optional[float] = None
    min_price_drop_pct: Optional[float] = None
    require_historical_low: bool = False
    condition_operator: str = "AND"
    require_in_stock: bool = True
    radius_km: float = Field(10.0, le=20.0)
    expansion_strategy: str = "NEARBY_FIRST"
    ranking_strategy: str = "BEST_DISCOUNT"
    cooldown_hours: float = 24.0
    lat: Optional[float] = None
    lng: Optional[float] = None
    local_store_id: Optional[str] = None
    telegram_recipient_ids: List[str] = Field(default_factory=list)
    run_interval_minutes: int = 0


class AlertRuleUpdate(BaseModel):
    enabled: Optional[bool] = None
    name: Optional[str] = None
    cooldown_hours: Optional[float] = None
    telegram_recipient_ids: Optional[List[str]] = None


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    categories: List[str]
    keywords: List[str]
    exclude_keywords: List[str]
    product_urls: List[str]
    min_discount_pct: Optional[float]
    max_price: Optional[float]
    min_price_drop_pct: Optional[float]
    require_historical_low: bool
    condition_operator: str
    require_in_stock: bool
    radius_km: float
    expansion_strategy: str
    ranking_strategy: str
    platform: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    cooldown_hours: float
    lat: Optional[float] = None
    lng: Optional[float] = None
    local_store_id: Optional[str] = None
    telegram_recipient_ids: List[str]
    run_interval_minutes: int


class AlertEventResponse(BaseModel):
    id: str
    alert_rule_id: str
    canonical_product_id: Optional[str] = None
    instamart_product_id: str
    product_name: str
    product_url: Optional[str] = None
    store_id: str
    store_name: Optional[str] = None
    distance_km: Optional[float] = None
    price: float
    mrp: float
    discount_percent: float
    previous_price: Optional[float] = None
    price_drop_percent: Optional[float] = None
    trigger_reason: str
    triggered_at: datetime
    notification_status: str


# ─── Price History Schemas ────────────────────────────────────────────────────

class PriceObservationResponse(BaseModel):
    id: Optional[str] = None
    instamart_product_id: str
    store_id: str
    observed_price: float
    mrp: float
    discount_percent: float
    in_stock: bool
    timestamp: datetime
