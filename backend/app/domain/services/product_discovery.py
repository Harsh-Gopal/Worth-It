from typing import List
import httpx
from app.platforms.instamart.client import search
from app.domain.models.product import CanonicalProduct
from app.domain.services.product_matcher import ProductMatcher

class ProductDiscoveryEngine:
    """
    Takes a broad keyword and discovers exact product variations by searching locally.
    """
    def __init__(self, client: httpx.Client, store_id: str):
        self.client = client
        self.store_id = store_id

    def discover(self, keyword: str, match_keywords: List[str] = None, exclude_keywords: List[str] = None) -> List[CanonicalProduct]:
        """
        Search the local store for the keyword, then run it through the matcher.
        Returns a list of CanonicalProducts representing exact variations.
        """
        matcher = ProductMatcher(keyword, match_keywords, exclude_keywords)
        
        # Broad search at the local store
        raw_products = search(self.client, self.store_id, keyword)
        
        canonical_products = []
        seen_ids = set()
        
        for p in raw_products:
            if matcher.matches(p):
                canonical = matcher.create_canonical(p)
                if canonical.id not in seen_ids:
                    canonical_products.append(canonical)
                    seen_ids.add(canonical.id)
                    
        return canonical_products
