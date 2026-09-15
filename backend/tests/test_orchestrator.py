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
    c = StoreCache(tmp_path / "test_orchestrator.db")
    yield c
    c.close()

# We mock ProductDiscoveryEngine, StoreDiscoveryService, and product_at_store
@pytest.mark.asyncio
@patch("app.domain.services.search_orchestrator.ProductDiscoveryEngine")
@patch("app.domain.services.search_orchestrator.product_at_store")
@patch("app.domain.services.search_orchestrator.StoreDiscoveryService")
async def test_orchestrator_nearby_first_early_stopping(
    mock_store_discovery,
    mock_product_at_store,
    mock_product_discovery,
    store_cache
):
    # Setup mock Discovery Engine
    mock_discovery_instance = MagicMock()
    # Discover one canonical product
    mock_discovery_instance.discover.return_value = [
        CanonicalProduct(id="canonical_123", brand="Nutrabay", normalized_name="nutrabay protein", category="supplements")
    ]
    mock_product_discovery.return_value = mock_discovery_instance
    
    # Setup mock store discovery
    mock_store_discovery_instance = MagicMock()
    # Mock finding two stores at different coordinates
    def mock_discover(lat, lng):
        # We will be passed lat/lng from hex grid
        return Store(external_store_id=f"store_{lat}", platform="instamart", name="Test", lat=lat, lng=lng)
    
    mock_store_discovery_instance.discover_store.side_effect = mock_discover
    mock_store_discovery.return_value = mock_store_discovery_instance

    # Setup mock product_at_store
    # Local store (store_local) -> No deal (20% discount)
    # Store at 3km (store_3km) -> Deal (55% discount)
    def mock_pas(client, store_id, ext_id):
        if store_id == "store_local":
            return InstamartProduct(external_product_id="123", name="Nutrabay Protein", url="", price=800, mrp=1000, stock=True, category="")
        else:
            return InstamartProduct(external_product_id="123", name="Nutrabay Protein", url="", price=450, mrp=1000, stock=True, category="")
            
    mock_product_at_store.side_effect = mock_pas

    client = MagicMock()
    orchestrator = DealSearchOrchestrator(
        client=client, 
        store_cache=store_cache, 
        center_lat=12.97, center_lng=77.59, 
        local_store_id="store_local"
    )

    condition = DealCondition(min_discount_pct=50.0)
    
    events = []
    async for event in orchestrator.run_search("search_1", "nutrabay protein", condition=condition, expansion_radii_km=[3.0, 5.0, 10.0], strategy="NEARBY_FIRST"):
        events.append(event)
        
    event_types = [e["event"] for e in events]
    
    # Assertions
    assert "local_search_started" in event_types
    assert "product_discovered" in event_types
    assert "local_search_completed" in event_types
    assert "radius_expansion_started" in event_types
    assert "radius_scan_started" in event_types
    assert "deal_found" in event_types
    
    # Verify early stopping
    # The deal is found at 3km, so it should NOT scan 5km or 10km.
    radius_scans = [e for e in events if e["event"] == "radius_scan_started"]
    assert len(radius_scans) == 1
    assert radius_scans[0]["data"]["radius_km"] == 3.0

    # Ensure search_completed message indicates early stopping
    completed_events = [e for e in events if e["event"] == "search_completed"]
    assert len(completed_events) == 1
    assert "Stopping early" in completed_events[0]["data"]["message"]

@pytest.mark.asyncio
@patch("app.domain.services.search_orchestrator.ProductDiscoveryEngine")
@patch("app.domain.services.search_orchestrator.product_at_store")
async def test_orchestrator_local_deal_stops_immediately(
    mock_product_at_store,
    mock_product_discovery,
    store_cache
):
    # Setup mock Discovery Engine
    mock_discovery_instance = MagicMock()
    mock_discovery_instance.discover.return_value = [
        CanonicalProduct(id="canonical_123", brand="Nutrabay", normalized_name="nutrabay protein", category="supplements")
    ]
    mock_product_discovery.return_value = mock_discovery_instance
    
    # Local store HAS the deal
    mock_product_at_store.return_value = InstamartProduct(
        external_product_id="123", name="Nutrabay Protein", url="", price=400, mrp=1000, stock=True, category=""
    )
    
    client = MagicMock()
    orchestrator = DealSearchOrchestrator(
        client=client, 
        store_cache=store_cache, 
        center_lat=12.97, center_lng=77.59, 
        local_store_id="store_local"
    )

    condition = DealCondition(min_discount_pct=50.0)
    
    events = []
    async for event in orchestrator.run_search("search_1", "nutrabay protein", condition=condition, expansion_radii_km=[3.0, 5.0, 10.0], strategy="NEARBY_FIRST"):
        events.append(event)
        
    event_types = [e["event"] for e in events]
    
    # Assertions
    assert "deal_found" in event_types
    assert "radius_expansion_started" not in event_types
    assert "radius_scan_started" not in event_types
