import re
from typing import List
from app.domain.models.product import InstamartProduct, CanonicalProduct

class ProductMatcher:
    def __init__(self, query: str, match_keywords: List[str] = None, exclude_keywords: List[str] = None):
        self.original_query = query
        if match_keywords:
            self.query_tokens = set([k.lower() for k in match_keywords])
        else:
            self.query_tokens = set(re.findall(r'\w+', query.lower()))
            
        self.exclude_tokens = set([k.lower() for k in exclude_keywords]) if exclude_keywords else set()

    def matches(self, product: InstamartProduct) -> bool:
        """
        Deterministically match the product against the query.
        For V1, we ensure all query tokens exist in the product name/brand,
        and filter out common unwanted categories if the user didn't ask for them.
        """
        name_lower = product.name.lower()
        
        # Check explicit exclude_keywords
        for ex_token in self.exclude_tokens:
            if ex_token in name_lower:
                return False
        
        # Check for negative keywords if not explicitly in the query
        negative_keywords = ["shaker", "bar", "cookie", "bottle"]
        for neg in negative_keywords:
            if neg in name_lower and neg not in self.query_tokens:
                return False

        # Ensure all query tokens are present in the product name
        name_tokens = set(re.findall(r'\w+', name_lower))
        for token in self.query_tokens:
            # We can do substring match for partial words or exact token match
            if not any(token in n_token for n_token in name_tokens):
                return False
                
        return True

    def create_canonical(self, product: InstamartProduct) -> CanonicalProduct:
        return CanonicalProduct(
            id=f"canonical_{product.external_product_id}",
            brand="Unknown", # Extract from name if possible
            normalized_name=product.name.lower(),
            category=product.category
        )
