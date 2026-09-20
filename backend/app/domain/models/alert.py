from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class AlertRule(BaseModel):
    id: str
    name: str = ""  # Human-readable alert name
    categories: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    product_urls: list[str] = Field(default_factory=list)  # Wishlist: exact Instamart product URLs
    min_discount_pct: Optional[float] = None
    max_price: Optional[float] = None
    min_price_drop_pct: Optional[float] = None
    require_historical_low: bool = False
    condition_operator: str = "AND"  # "AND" or "OR"
    require_in_stock: bool = True
    radius_km: float = 10.0
    expansion_strategy: str = "NEARBY_FIRST"
    ranking_strategy: str = "BEST_DISCOUNT"
    platform: str = "instamart"
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    cooldown_hours: float = 24.0
    lat: Optional[float] = None
    lng: Optional[float] = None
    local_store_id: Optional[str] = None
    # Telegram: list of chat IDs to notify for this specific alert
    telegram_recipient_ids: list[str] = Field(default_factory=list)
    # Alert run interval in minutes (0 = use global scheduler interval)
    run_interval_minutes: int = 0

class AlertEvent(BaseModel):
    id: str
    alert_rule_id: str
    canonical_product_id: Optional[str] = None
    instamart_product_id: str
    product_name: str = ""  # Display name
    product_url: Optional[str] = None  # Direct link
    product_image: Optional[str] = None
    platform: str = "instamart"
    store_id: str
    store_name: Optional[str] = None
    store_pincode: Optional[str] = None
    search_pincode: Optional[str] = None
    distance_km: Optional[float] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    price: float
    mrp: float
    discount_percent: float
    previous_price: Optional[float] = None
    price_drop_percent: Optional[float] = None
    trigger_reason: str
    triggered_at: datetime = Field(default_factory=utc_now)
    notification_status: str = "pending"  # pending, sent, failed
    notification_attempts: int = 0

class NotificationResult(BaseModel):
    success: bool
    provider: str
    timestamp: datetime = Field(default_factory=utc_now)
    error_message: Optional[str] = None
    retryable: bool = False
