from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class DealLevel(str, Enum):
    NORMAL = "NORMAL"
    GOOD = "GOOD"
    GREAT = "GREAT"
    EXCEPTIONAL = "EXCEPTIONAL"


class DealThresholds(BaseModel):
    """
    Defines the minimum discount percentages required to hit each deal level.
    """
    min_discount_pct: float = 15.0
    good_discount_pct: Optional[float] = None
    great_discount_pct: Optional[float] = None
    exceptional_discount_pct: Optional[float] = None

    def evaluate_level(self, discount: float) -> DealLevel:
        if self.exceptional_discount_pct is not None and discount >= self.exceptional_discount_pct:
            return DealLevel.EXCEPTIONAL
        if self.great_discount_pct is not None and discount >= self.great_discount_pct:
            return DealLevel.GREAT
        if self.good_discount_pct is not None and discount >= self.good_discount_pct:
            return DealLevel.GOOD
        if discount >= self.min_discount_pct:
            return DealLevel.GOOD # Fallback
        return DealLevel.NORMAL


class CategoryDealRule(DealThresholds):
    category_name: str


class KeywordDealRule(DealThresholds):
    keyword: str


class ProductDealRule(DealThresholds):
    product_identifier: str  # Could be URL, ID, or name
