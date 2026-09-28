import re
from typing import List
from app.domain.models.product import PlatformProduct, CanonicalProduct

class ProductMatcher:
    def __init__(self, query: str, match_keywords: List[str] = None, exclude_keywords: List[str] = None, exclude_keyword_rules: dict = None):
        self.original_query = query
        if match_keywords:
            self.query_tokens = set([k.lower() for k in match_keywords])
        else:
            self.query_tokens = set(re.findall(r'\w+', query.lower()))
            
        self.exclude_tokens = set([k.lower() for k in exclude_keywords]) if exclude_keywords else set()
        self.exclude_keyword_rules = exclude_keyword_rules or {}

    def matches(self, product: PlatformProduct) -> bool:
        """
        Deterministically match the product against the query.
        For V1, we ensure all query tokens exist in the product name/brand,
        and filter out common unwanted categories if the user didn't ask for them.
        """
        name_lower = product.name.lower()
        
        # Check explicit exclude_keywords with discount threshold
        discount = 0.0
        if product.mrp > 0 and product.price < product.mrp:
            discount = ((product.mrp - product.price) / product.mrp) * 100.0

        for ex_token in self.exclude_tokens:
            if ex_token in name_lower:
                rule = self.exclude_keyword_rules.get(ex_token, {})
                threshold = rule.get("min_discount_pct") if isinstance(rule, dict) else None
                
                if threshold is not None:
                    # Exclude ONLY if discount <= threshold
                    if discount <= threshold:
                        return False
                else:
                    # "Never" mode (or no threshold set): always exclude
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

    def create_canonical(self, product: PlatformProduct) -> CanonicalProduct:
        return CanonicalProduct(
            id=f"canonical_{product.external_product_id}",
            brand="Unknown", # Extract from name if possible
            normalized_name=product.name.lower(),
            category=getattr(product, "category", "Unknown")
        )
