from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class PriceObservation(BaseModel):
    id: Optional[str] = None
    canonical_product_id: Optional[str] = None
    instamart_product_id: str
    store_id: str
    observed_price: float
    mrp: float
    discount_percent: float
    in_stock: bool
    timestamp: datetime = Field(default_factory=utc_now)
