from dataclasses import dataclass
from typing import Dict

@dataclass
class PlatformCapabilities:
    platform: str
    api_available: bool
    playwright_available: bool
    requires_browser: bool
    product_url_supported: bool
    keyword_search_supported: bool
    category_search_supported: bool
    store_discovery_supported: bool
    serviceability_supported: bool
    enabled: bool = True
    rate_limit: float = 1.0
    max_concurrency: int = 3
    request_timeout: float = 15.0

PLATFORM_CAPABILITIES: Dict[str, PlatformCapabilities] = {
    "zepto": PlatformCapabilities(
        platform="zepto",
        api_available=False,
        playwright_available=True,
        requires_browser=True,
        product_url_supported=True,
        keyword_search_supported=True,
        category_search_supported=True,
        store_discovery_supported=True,
        serviceability_supported=True,
        max_concurrency=3
    ),
    "swiggy": PlatformCapabilities(
        platform="swiggy",
        api_available=True,
        playwright_available=True,
        requires_browser=False, # HTTP adapter exists for primary operations
        product_url_supported=True,
        keyword_search_supported=True,
        category_search_supported=True,
        store_discovery_supported=True,
        serviceability_supported=True,
        max_concurrency=6
    ),
    "blinkit": PlatformCapabilities(
        platform="blinkit",
        api_available=True,
        playwright_available=False,
        requires_browser=False,
        product_url_supported=True,
        keyword_search_supported=True,
        category_search_supported=True,
        store_discovery_supported=True,
        serviceability_supported=True,
        max_concurrency=5
    ),
    "minutes": PlatformCapabilities(
        platform="minutes",
        api_available=False,
        playwright_available=True,
        requires_browser=True,
        product_url_supported=True,
        keyword_search_supported=True,
        category_search_supported=True,
        store_discovery_supported=False, # Minutes relies on Pincode
        serviceability_supported=True,
        max_concurrency=3
    ),
    "flipkart": PlatformCapabilities(
        platform="flipkart",
        api_available=True,
        playwright_available=False,
        requires_browser=False,
        product_url_supported=True,
        keyword_search_supported=True,
        category_search_supported=True,
        store_discovery_supported=False,
        serviceability_supported=True,
        max_concurrency=3
    )
}

def get_capabilities(platform: str) -> PlatformCapabilities:
    return PLATFORM_CAPABILITIES.get(platform.lower())

def is_playwright_allowed(platform: str, global_playwright_enabled: bool) -> bool:
    """Return True if this platform is allowed to run in the current environment.
    
    Platforms that REQUIRE a browser (requires_browser=True) are only allowed when
    Playwright is globally enabled.  API-based platforms (requires_browser=False)
    are always allowed regardless of the Playwright setting.
    """
    caps = get_capabilities(platform)
    if not caps:
        # Unknown platform — allow it; the platform itself will fail gracefully.
        return True
    if caps.requires_browser:
        # Browser-required platforms need Playwright to be enabled globally.
        return global_playwright_enabled
    # API-based platform — always allowed.
    return True
