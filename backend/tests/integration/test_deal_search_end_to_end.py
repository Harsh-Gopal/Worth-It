import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

from app.domain.models.deal import DealCondition
from app.domain.models.product import CanonicalProduct, InstamartProduct
from app.domain.models.store import Store
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.geo.store_cache import StoreCache

@pytest.fixture
def store_cache(tmp_path):
    c = StoreCache(tmp_path / "test_e2e.db")
    yield c
    c.close()

@pytest.mark.asyncio
@patch("app.domain.services.search_orchestrator.ProductDiscoveryEngine")
@patch("app.domain.services.search_orchestrator.product_at_store")
@patch("app.domain.services.search_orchestrator.StoreDiscoveryService")
async def test_e2e_geographic_expansion_and_deal_found(
    mock_store_discovery,
    mock_product_at_store,
    mock_product_discovery,
    store_cache
):
    """
    Scenario:
    Local Store: No Deal
    3km: No Deal
    5km: Store D has 52.5% discount deal.
    """
    # 1. Mock Local Product Discovery
    mock_discovery = MagicMock()
    mock_discovery.discover.return_value = [
        CanonicalProduct(id="canonical_123", brand="Nutrabay", normalized_name="nutrabay protein", category="supplements")
    ]
    mock_product_discovery.return_value = mock_discovery

    # 2. Mock Store Discovery
    mock_store_service = MagicMock()
    # We just return a unique store for each probe
    def mock_discover(lat, lng):
        return Store(external_store_id=f"store_{lat}_{lng}", platform="instamart", name="Test", lat=lat, lng=lng)
    mock_store_service.discover_store.side_effect = mock_discover
    mock_store_discovery.return_value = mock_store_service

    # 3. Mock product_at_store
    def mock_pas(client, store_id, ext_id):
        if store_id == "store_local":
            return InstamartProduct(external_product_id="123", name="Nutrabay", url="", price=3000, mrp=4000, stock=True, category="")
        else:
            # We will artificially inject a deal if the store is part of the 5km hex grid 
            # (which means it's one of the discovered stores during the second expansion loop)
            # Just say the first store checked in the 5km radius gives the 52.5% discount.
            if "store_13" in store_id: # A crude way to identify expanded hex points
                return InstamartProduct(external_product_id="123", name="Nutrabay", url="", price=1900, mrp=4000, stock=True, category="")
            # Otherwise no deal
            return InstamartProduct(external_product_id="123", name="Nutrabay", url="", price=2800, mrp=4000, stock=True, category="")
            
    mock_product_at_store.side_effect = mock_pas

    client = MagicMock()
    orchestrator = DealSearchOrchestrator(
        client=client, store_cache=store_cache, 
        center_lat=12.97, center_lng=77.59, 
        local_store_id="store_local"
    )

    condition = DealCondition(min_discount_pct=50.0)
    
    events = []
    async for event in orchestrator.run_search("search_1", "nutrabay protein", condition=condition, expansion_radii_km=[3.0, 5.0, 10.0]):
        events.append(event)
        
    event_types = [e["event"] for e in events]
    
    # Assertions
    assert "deal_found" in event_types
    # Verify we hit the 5km radius, but didn't scan 10km (EARLY STOPPING)
    radii_scanned = [e["data"]["radius_km"] for e in events if e["event"] == "radius_scan_started"]
    assert 3.0 in radii_scanned
    assert 5.0 in radii_scanned
    assert 10.0 not in radii_scanned
    
    # Check that DealEngine calculated 52.5% correctly
    deal_events = [e for e in events if e["event"] == "deal_found"]
    assert len(deal_events) >= 1
    assert deal_events[0]["data"]["discount_percent"] == 52.5

@pytest.mark.asyncio
@patch("app.domain.services.search_orchestrator.ProductDiscoveryEngine")
@patch("app.domain.services.search_orchestrator.product_at_store")
@patch("app.domain.services.search_orchestrator.StoreDiscoveryService")
async def test_e2e_cancellation_and_failure_isolation(
    mock_store_discovery,
    mock_product_at_store,
    mock_product_discovery,
    store_cache
):
    """
    Scenario:
    Local store fails targeted check (403 or exception).
    Radius expansion begins.
    User cancels mid-expansion.
    """
    mock_discovery = MagicMock()
    mock_discovery.discover.return_value = [
        CanonicalProduct(id="canonical_123", brand="Nutrabay", normalized_name="nutrabay", category="supplements")
    ]
    mock_product_discovery.return_value = mock_discovery
    
    # Mock store discovery to sleep, ensuring cancellation happens during geographic expansion
    mock_store_service = MagicMock()
    async def mock_discover(lat, lng):
        await asyncio.sleep(0.5)
        return Store(external_store_id=f"store_{lat}_{lng}", platform="instamart", name="Test", lat=lat, lng=lng)
    
    # Since discover_store is called via asyncio.to_thread, we just make it a normal slow blocking function
    def sync_mock_discover(lat, lng):
        import time
        time.sleep(0.5)
        return Store(external_store_id=f"store_{lat}_{lng}", platform="instamart", name="Test", lat=lat, lng=lng)
        
    mock_store_service.discover_store.side_effect = sync_mock_discover
    mock_store_discovery.return_value = mock_store_service
    
    # Simulate a network failure on targeted fetch
    mock_product_at_store.side_effect = Exception("HTTP 403 Forbidden")
    
    client = MagicMock()
    orchestrator = DealSearchOrchestrator(
        client=client, store_cache=store_cache, 
        center_lat=12.97, center_lng=77.59, 
        local_store_id="store_local"
    )

    cancel_event = asyncio.Event()
    condition = DealCondition(min_discount_pct=50.0)
    
    events = []
    
    async def cancel_soon():
        await asyncio.sleep(0.1)
        cancel_event.set()
        
    asyncio.create_task(cancel_soon())
    
    async for event in orchestrator.run_search("search_2", "nutrabay protein", condition=condition, cancel_event=cancel_event):
        events.append(event)
        
    event_types = [e["event"] for e in events]
    
    # Verify Failure Isolation: the exception was caught and emitted as a failed check
    assert "product_check_failed" in event_types
    
    # Verify Cancellation: we eventually emit a search_cancelled event
    assert "search_cancelled" in event_types
    # Make sure we didn't artificially emit a successful search_completed
    assert "search_completed" not in event_types
