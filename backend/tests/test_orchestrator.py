"""Tests for DealSearchOrchestrator.

Adapted to the actual implementation:
- ProductDiscoveryEngine.discover() returns [] (disabled due to Swiggy WAF)
- _async_product_at_store uses the SwiggyClient directly
- StoreDiscoveryService does not exist; _async_discover_store is an internal method
- The orchestrator yields SSE event dicts
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import AsyncIterator, Dict

from app.domain.models.deal import DealCondition
from app.domain.models.product import CanonicalProduct, PlatformProduct
from app.domain.services.search_orchestrator import DealSearchOrchestrator, _DiscoveredStore
from app.geo.store_cache import StoreCache, Store


@pytest.fixture
def store_cache(tmp_path):
    c = StoreCache(tmp_path / "test_orchestrator.db")
    yield c
    c.close()


def _make_orchestrator(store_cache, center_lat=12.97, center_lng=77.59, local_store_id="store_local"):
    """Create an orchestrator with a mock SwiggyClient."""
    client = AsyncMock()
    type(client).platform_name = PropertyMock(return_value="mock_platform")
    # resolve_store returns a StoreResolution-like mock
    from app.platforms.base import StoreResolution
    client.resolve_store = AsyncMock(return_value=StoreResolution(
        serviceable=True, store_id="synthetic_12.97_77.59", store_name="Instamart"
    ))
    return DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=center_lat,
        center_lng=center_lng,
        local_store_id=local_store_id,
    ), client


@pytest.mark.asyncio
async def test_orchestrator_search_no_products_found(store_cache):
    """When ProductDiscoveryEngine finds nothing, orchestrator emits search_error."""
    orch, _ = _make_orchestrator(store_cache)

    # Mock discovery to return empty list (Swiggy WAF blocks it; this is the real behavior)
    with patch("app.domain.services.search_orchestrator.ProductDiscoveryEngine") as MockPDE:
        mock_pde = AsyncMock()
        mock_pde.discover.return_value = []
        MockPDE.return_value = mock_pde

        events = []
        async for event in orch.run_search("search-1", "nonexistent product"):
            events.append(event)

    event_types = [e["event"] for e in events]
    assert "search_started" in event_types
    assert "search_error" in event_types


@pytest.mark.asyncio
async def test_orchestrator_keyword_search_with_mock_discovery(store_cache):
    """When a canonical product IS found, orchestrator checks local store and emits deal_found if criteria met."""
    orch, client = _make_orchestrator(store_cache)

    # Mock discovery to return one candidate
    mock_canonical = CanonicalProduct(
        id="canonical_PROD123",
        brand="TestBrand",
        normalized_name="test protein",
        category="supplements",
    )

    # Mock product_at_store on the client to return an in-stock product with 60% discount
    from app.platforms.base import ProductResult
    client.product_at_store = AsyncMock(return_value=ProductResult(
        status="in_stock",
        name="Test Protein 1kg",
        price=400.0,
        mrp=1000.0,
        external_product_id="PROD123",
    ))

    with patch("app.domain.services.search_orchestrator.ProductDiscoveryEngine") as MockPDE:
        mock_pde = AsyncMock()
        mock_pde.discover.return_value = [mock_canonical]
        MockPDE.return_value = mock_pde

        events = []
        condition = DealCondition(require_in_stock=True)
        async for event in orch.run_search(
            "search-2", "test protein",
            condition=condition,
            expansion_radii_km=[3.0],
            strategy="NEARBY_FIRST",
        ):
            events.append(event)

    event_types = [e["event"] for e in events]
    assert "search_started" in event_types
    assert "product_discovered" in event_types
    assert "deal_found" in event_types

    # NEARBY_FIRST + local deal found → no radius expansion
    assert "radius_expansion_started" not in event_types


@pytest.mark.asyncio
async def test_orchestrator_discovered_store_uses_correct_field(store_cache):
    """_async_discover_store must use StoreResolution.store_id (NOT external_store_id)."""
    orch, _ = _make_orchestrator(store_cache)

    from app.platforms.base import StoreResolution
    # Build a StoreResolution that only has store_id (the correct field)
    res = StoreResolution(serviceable=True, store_id="real_store_id_abc", store_name="Test Instamart")
    assert hasattr(res, "store_id"), "StoreResolution must have store_id"
    assert not hasattr(res, "external_store_id"), "StoreResolution must NOT have external_store_id"

    # Patch client.resolve_store to return this
    orch.client.resolve_store = AsyncMock(return_value=res)

    result = await orch._async_discover_store(12.97, 77.59)
    assert result is not None
    assert isinstance(result, _DiscoveredStore)
    assert result.store_id == "real_store_id_abc"
    assert result.probe_lat == pytest.approx(12.97)
    assert result.probe_lng == pytest.approx(77.59)


def test_discovered_store_dataclass():
    """_DiscoveredStore carries probe coords, not store coords (StoreResolution has no lat/lng)."""
    ds = _DiscoveredStore(
        store_id="abc123",
        store_name="My Store",
        probe_lat=12.97,
        probe_lng=77.59,
    )
    assert ds.store_id == "abc123"
    assert ds.probe_lat == pytest.approx(12.97)
