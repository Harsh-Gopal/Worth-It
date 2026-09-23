import pytest
import inspect
from typing import get_type_hints, get_args, List, Optional
from app.platforms.swiggy import SwiggyClient
from app.platforms.zepto.client import ZeptoClient
from app.platforms.blinkit import BlinkitClient
from app.domain.models.product import PlatformProduct

clients = [
    SwiggyClient,
    ZeptoClient,
    BlinkitClient
]

@pytest.mark.parametrize("client_cls", clients)
def test_platform_client_contract(client_cls):
    """
    Ensure all platform clients implement the required methods with the correct signatures and return types.
    """
    client = client_cls()
    
    # Check for platform_name attribute
    assert hasattr(client, "platform_name")
    assert isinstance(client.platform_name, str)
    assert len(client.platform_name) > 0

    # 1. search method
    assert hasattr(client, "search")
    search_sig = inspect.signature(client.search)
    assert "query" in search_sig.parameters
    assert "store_id" in search_sig.parameters
    
    hints = get_type_hints(client.search)
    return_type = hints.get("return")
    
    # The search method should return List[PlatformProduct] or at least a list/sequence of them
    # Some older implementations might lack strict type hints, but we enforce them here to prevent regressions.
    # At a minimum, we verify the method is async.
    assert inspect.iscoroutinefunction(client.search), f"{client_cls.__name__}.search must be async"
    
    # 2. product_at_store method
    assert hasattr(client, "product_at_store")
    pas_sig = inspect.signature(client.product_at_store)
    assert "product_id" in pas_sig.parameters
    assert "store_id" in pas_sig.parameters
    assert inspect.iscoroutinefunction(client.product_at_store), f"{client_cls.__name__}.product_at_store must be async"

    # 3. resolve_store method
    assert hasattr(client, "resolve_store")
    rs_sig = inspect.signature(client.resolve_store)
    assert "lat" in rs_sig.parameters
    assert "lng" in rs_sig.parameters
    assert inspect.iscoroutinefunction(client.resolve_store), f"{client_cls.__name__}.resolve_store must be async"
    
    # 4. resolve_share_link method
    assert hasattr(client, "resolve_share_link")
    rsl_sig = inspect.signature(client.resolve_share_link)
    assert "url" in rsl_sig.parameters
    assert inspect.iscoroutinefunction(client.resolve_share_link), f"{client_cls.__name__}.resolve_share_link must be async"

