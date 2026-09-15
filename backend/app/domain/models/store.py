from pydantic import BaseModel
from typing import Optional

class Store(BaseModel):
    """
    A geographic store location.
    """
    platform: str            # Always "instamart" for V1
    external_store_id: str   # Instamart's storeId
    name: Optional[str] = None
    pincode: Optional[str] = None
    lat: float
    lng: float
    distance_km: Optional[float] = None
