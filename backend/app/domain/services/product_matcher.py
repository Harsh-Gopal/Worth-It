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

        # Ensure all query tokens are present in the product name or category
        name_tokens = set(re.findall(r'\w+', name_lower))
        category_lower = getattr(product, "category", "").lower()
        cat_tokens = set(re.findall(r'\w+', category_lower))
        all_text_tokens = name_tokens.union(cat_tokens)
        
        for token in self.query_tokens:
            # Check for substring match in either direction to handle plurals/variants
            # e.g., "chocolates" in query should match "chocolate" in product name
            matched = False
            for text_token in all_text_tokens:
                if token in text_token or text_token in token:
                    # To prevent tiny tokens like "a" matching everything, enforce minimum length
                    if len(token) > 2 and len(text_token) > 2:
                        matched = True
                        break
                    elif token == text_token:
                        matched = True
                        break
            if not matched:
                return False
                
        return True

    def create_canonical(self, product: InstamartProduct) -> CanonicalProduct:
        return CanonicalProduct(
            id=f"canonical_{product.external_product_id}",
            brand="Unknown", # Extract from name if possible
            normalized_name=product.name.lower(),
            category=getattr(product, "category", "Unknown")
        )
