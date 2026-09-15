import httpx
from typing import Optional
from app.domain.models.store import Store
from app.platforms.instamart.client import select_store
import logging

log = logging.getLogger(__name__)

class StoreDiscoveryService:
    def __init__(self, client: httpx.Client):
        self.client = client

    def discover_store(self, lat: float, lng: float, address: str = "") -> Optional[Store]:
        """
        Takes coordinates and resolves them to an Instamart Store.
        """
        # If we don't have a reverse-geocoded address, use a dummy one
        if not address:
            address = f"Location {lat},{lng}"
            
        place = {
            "lat": lat,
            "lng": lng,
            "address": address,
            "title": address
        }
        
        try:
            store_id = select_store(self.client, place)
            if store_id:
                return Store(
                    external_store_id=store_id,
                    platform="instamart",
                    name=None,
                    pincode=None,
                    lat=lat,
                    lng=lng
                )
        except LookupError as e:
            # Expected if the area is unserviceable
            log.debug(f"Store discovery failed for {lat},{lng}: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error discovering store at {lat},{lng}: {e}")
            return None
            
        return None
