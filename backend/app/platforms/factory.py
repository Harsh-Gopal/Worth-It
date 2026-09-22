import logging
from typing import Dict, Type

from app.platforms.base import PlatformClient
from app.platforms.swiggy import SwiggyClient
from app.platforms.zepto.client import ZeptoClient
from app.platforms.blinkit import BlinkitClient

log = logging.getLogger("platform_factory")

_PLATFORM_REGISTRY: Dict[str, Type[PlatformClient]] = {
    "swiggy": SwiggyClient,
    "zepto": ZeptoClient,
    "blinkit": BlinkitClient,
}

def get_platform_client(platform: str, **kwargs) -> PlatformClient:
    """Instantiate and return the appropriate PlatformClient for the given platform."""
    platform = platform.lower()
    client_cls = _PLATFORM_REGISTRY.get(platform)
    
    if not client_cls:
        raise ValueError(f"Unknown platform requested: {platform}")
        
    return client_cls(**kwargs)

def get_all_platforms() -> list[str]:
    """Return a list of all registered platform identifiers."""
    return list(_PLATFORM_REGISTRY.keys())
