from typing import Optional, Dict, Any
from datetime import datetime

from app.domain.models.product import InstamartProduct
from app.domain.models.price_observation import PriceObservation
from app.persistence.repositories.price_history_repo import PriceHistoryRepository

class PriceHistoryService:
    def __init__(self, repo: PriceHistoryRepository):
        self.repo = repo

    def record_observation(self, product: InstamartProduct, store_id: str) -> PriceObservation:
        discount = 0.0
        if product.mrp > 0 and product.price > 0 and product.price <= product.mrp:
            discount = round(((product.mrp - product.price) / product.mrp) * 100, 1)
            
        obs = PriceObservation(
            canonical_product_id=product.canonical_product_id,
            instamart_product_id=product.external_product_id,
            store_id=store_id,
            observed_price=product.price,
            mrp=product.mrp,
            discount_percent=discount,
            in_stock=product.stock
        )
        return self.repo.record_observation(obs)

    def get_history_context(self, product: InstamartProduct, store_id: str, current_obs: PriceObservation) -> Dict[str, Any]:
        """
        Retrieves the historical context for a given product at a store BEFORE the current observation.
        """
        # Find previous observation before this timestamp
        prev_obs = self.repo.get_previous_observation(
            product.external_product_id, 
            store_id, 
            current_obs.timestamp
        )
        
        # Find historical low before this timestamp
        historical_low = self.repo.get_historical_low(
            product.external_product_id, 
            store_id, 
            current_obs.timestamp
        )
        
        # We also need overall historical low (including current) to see if we just set a new low
        overall_low = self.repo.get_historical_low(
            product.external_product_id,
            store_id,
            None # all time
        )

        previous_price = prev_obs.observed_price if prev_obs else None
        
        price_drop_pct = None
        if previous_price and previous_price > current_obs.observed_price:
            price_drop_pct = round(((previous_price - current_obs.observed_price) / previous_price) * 100, 2)
            
        is_historical_low = False
        if overall_low is not None and current_obs.observed_price <= overall_low:
            # If there was no history before, it's technically a low, but maybe we only want to say it's a historical low if there IS history
            if historical_low is not None and current_obs.observed_price < historical_low:
                is_historical_low = True
                
        return {
            "previous_price": previous_price,
            "price_drop_percent": price_drop_pct,
            "historical_low_before_now": historical_low,
            "is_historical_low": is_historical_low
        }
