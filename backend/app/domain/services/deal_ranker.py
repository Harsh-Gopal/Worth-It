from typing import List, Dict, Any
from app.domain.models.deal import DealRankingStrategy

class DealRanker:
    """
    Ranks deal evaluations based on the user's strategy.
    """
    def __init__(self, strategy: str = "BEST_OVERALL"):
        self.strategy = strategy

    def rank(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts the SSE event dictionaries of 'deal_found'.
        """
        if not results:
            return []

        if self.strategy == DealRankingStrategy.BEST_PRICE or self.strategy == "BEST_PRICE":
            results.sort(key=lambda r: (
                r.get("price", float('inf')),
                r.get("distance_km", float('inf'))
            ))
        elif self.strategy == DealRankingStrategy.NEAREST or self.strategy == "NEAREST":
            results.sort(key=lambda r: (
                r.get("distance_km", float('inf')),
                r.get("price", float('inf'))
            ))
        elif self.strategy == DealRankingStrategy.BEST_DISCOUNT or self.strategy == "BEST_DISCOUNT":
            results.sort(key=lambda r: (
                -r.get("discount_pct", 0),
                r.get("price", float('inf'))
            ))
        elif self.strategy == DealRankingStrategy.BIGGEST_DROP or self.strategy == "BIGGEST_DROP":
            results.sort(key=lambda r: (
                -r.get("price_drop_pct", 0) if r.get("price_drop_pct") is not None else 0,
                r.get("price", float('inf'))
            ))
        else: # BEST_OVERALL
            # Priority 1: Lowest Price
            # Priority 2: Highest Discount
            # Priority 3: Nearest distance
            results.sort(key=lambda r: (
                r.get("price", float('inf')), 
                -r.get("discount_pct", 0), 
                r.get("distance_km", float('inf'))
            ))

        return results
