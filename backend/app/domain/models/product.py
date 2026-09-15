from pydantic import BaseModel
from typing import Optional

class CanonicalProduct(BaseModel):
    """
    A platform-agnostic representation of a product.
    Used for mapping a broad keyword to exact product variations.
    """
    id: str                  # Internal system ID
    brand: str
    normalized_name: str     # e.g., "nutrabay pure 100 raw whey protein concentrate"
    category: str
    size: Optional[str] = None
    variant: Optional[str] = None

class InstamartProduct(BaseModel):
    """
    The Instamart-specific representation of a product.
    """
    external_product_id: str  # Instamart's item ID
    canonical_product_id: Optional[str] = None
    name: str                 # Display name on Instamart
    url: str
    image_url: Optional[str] = None
    price: float              # Selling price (normalized to float)
    mrp: float                # Maximum Retail Price
    stock: bool
    category: str
