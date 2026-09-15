from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class DealRankingStrategy(str, Enum):
    BEST_PRICE = "BEST_PRICE"
    BEST_DISCOUNT = "BEST_DISCOUNT"
    NEAREST = "NEAREST"
    BIGGEST_DROP = "BIGGEST_DROP"
    BEST_OVERALL = "BEST_OVERALL"


class DealCondition(BaseModel):
    """
    Conditions that must ALL be met (AND) or ANY be met (OR) for a product to
    qualify as a deal. Each field is optional — omitting all fields means every
    in-stock product qualifies (discovery / browse mode).
    """
    min_discount_pct: Optional[float] = None
    max_price: Optional[float] = None
    price_drop_pct: Optional[float] = None
    require_historical_low: bool = False
    require_in_stock: bool = True        # default: only in-stock products qualify
    condition_operator: str = "AND"      # "AND" or "OR"


class DealEvaluation(BaseModel):
    """
    The result of evaluating an InstamartProduct against a DealCondition.
    """
    qualifies: bool
    discount_percent: float
    price: float
    mrp: float
    previous_price: Optional[float] = None
    price_drop_percent: Optional[float] = None
    historical_low: Optional[float] = None
    is_historical_low: bool = False
    trigger_reasons: List[str]  # e.g., ["Discount 34.0% ≥ 30.0%", "Historical low"]
