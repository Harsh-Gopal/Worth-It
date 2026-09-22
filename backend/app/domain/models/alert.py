from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.domain.models.intelligence import DealThresholds
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
    
    # Deal Intelligence Rules (Stored as JSON text mapping identifier to thresholds)
    category_rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    keyword_rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    product_rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    max_price: Optional[float] = None
    min_savings: Optional[float] = None
    adaptive_mode: bool = True
    min_price_drop_pct: Optional[float] = None
    require_historical_low: bool = False
    condition_operator: str = "AND"  # "AND" or "OR"
    require_in_stock: bool = True
    radius_km: float = 10.0
    search_mode: str = "current_pincode"
    expansion_strategy: str = "NEARBY_FIRST"
    ranking_strategy: str = "BEST_DISCOUNT"
    platforms: list[str] = Field(default_factory=lambda: ["swiggy"])
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_run_at: Optional[datetime] = None
    cooldown_hours: float = 24.0
    lat: Optional[float] = None
    lng: Optional[float] = None
    pincode: Optional[str] = None
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
    
    # Deal Intelligence outputs
    deal_level: Optional[str] = None
    deal_score: Optional[float] = None
    savings_amount: Optional[float] = None
    applicable_rule: Optional[str] = None
    
    trigger_reason: str
    triggered_at: datetime = Field(default_factory=utc_now)
    notification_status: str = "pending"  # pending, sent, failed, suppressed
    notification_attempts: int = 0
    scan_run_id: Optional[str] = None

class NotificationResult(BaseModel):
    success: bool
    provider: str
    timestamp: datetime = Field(default_factory=utc_now)
    error_message: Optional[str] = None
    retryable: bool = False

class GroupedAlertEvent(BaseModel):
    group_id: str
    instamart_product_id: str
    product_name: str
    product_image: Optional[str] = None
    platform: str = "instamart"
    category: Optional[str] = None
    best_price: float
    mrp: float
    best_discount_percent: float
    deal_level: Optional[str] = None
    deal_score: Optional[float] = None
    savings_amount: Optional[float] = None
    trigger_reason: str
    triggered_at: datetime
    local_date: str
    locations_count: int
    platforms_count: int = 1
    offers: List[AlertEvent]
    scan_run_id: Optional[str] = None
