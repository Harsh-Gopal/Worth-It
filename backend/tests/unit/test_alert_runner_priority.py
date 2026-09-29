import pytest
import asyncio
from typing import List, AsyncIterator
from app.domain.models.alert import AlertRule
from app.domain.models.events import OrchestratorEvent
from app.domain.services.alert_runner import AlertRunner
from app.geo.store_cache import StoreCache

class MockClient:
    def __init__(self, name, event_tracker):
        self.platform_name = name
        self.event_tracker = event_tracker

    async def resolve_store(self, lat, lng):
        class DummyStore:
            serviceable = True
            store_id = "test_store"
        return DummyStore()

    async def resolve_share_link(self, url):
        return "pid_123"

    async def aclose(self):
        pass

class MockOrchestrator:
    def __init__(self, client, store_cache=None, local_store_id=None, *args, **kwargs):
        self.client = client
        self.platform_name = client.platform_name
        self.store_cache = store_cache or type('MockStoreCache', (), {'stores_within': lambda *a: [], 'has_fresh_probe_near': lambda *a: False, 'record_probe': lambda *a: None})()
        self.local_store_id = local_store_id

    async def run_url_search(self, *args, **kwargs) -> AsyncIterator[OrchestratorEvent]:
        self.client.event_tracker.append(self.platform_name)
        # Yield a dummy event to simulate work
        yield OrchestratorEvent(event="search_completed", search_id="test", timestamp="2023-01-01")
        # Give control back to event loop to test concurrency vs sequential
        await asyncio.sleep(0.01)

    async def run_combined_search(self, *args, **kwargs) -> AsyncIterator[OrchestratorEvent]:
        # not used in this test
        pass

@pytest.mark.asyncio
async def test_alert_runner_sequential_platform_execution(monkeypatch):
    """
    Test that the alert runner executes platforms sequentially, and strictly 
    in the order they appear in the product_urls list.
    """
    event_tracker = []
    
    client_instamart = MockClient("instamart", event_tracker)
    client_zepto = MockClient("zepto", event_tracker)
    client_blinkit = MockClient("blinkit", event_tracker)
    
    # We patch DealSearchOrchestrator to use our MockOrchestrator
    import app.domain.services.alert_runner
    monkeypatch.setattr(app.domain.services.alert_runner, "DealSearchOrchestrator", MockOrchestrator)
    # Allow all platforms regardless of playwright_enabled so mock clients aren't skipped
    monkeypatch.setattr(app.domain.services.alert_runner, "is_playwright_allowed", lambda *a, **kw: True)
    
    # Mock link detection so we can route URLs to platforms
    def mock_detect_platform(url: str) -> str:
        if "swiggy" in url or "instamart" in url:
            return "instamart"
        if "zepto" in url:
            return "zepto"
        if "blinkit" in url:
            return "blinkit"
        return "unknown"
        
    monkeypatch.setattr("app.links.detect_platform", mock_detect_platform)
    
    class MockStoreCache:
        pincode = None
        def stores_within(self, *args, **kwargs):
            return []
        def has_fresh_probe_near(self, *args, **kwargs):
            return False
        def record_probe(self, *args, **kwargs):
            pass

    runner = AlertRunner(
        clients=[client_instamart, client_zepto, client_blinkit],
        store_cache=MockStoreCache(),
        center_lat=28.0,
        center_lng=77.0,
        local_store_id="123",
        alert_repo=type('MockAlertRepo', (), {'touch_rule': lambda self, *args: None})(),
        price_history=None,
        notification_service=None
    )
    # Give a dummy mock for broadcaster
    class MockBroadcaster:
        async def publish(self, *args, **kwargs):
            pass
    monkeypatch.setattr(app.domain.services.alert_runner, "broadcaster", MockBroadcaster())
    
    # Mock alert_engine
    class MockAlertEngine:
        def evaluate_deals(self, rule, deals, run_id):
            return []
        async def process_event(self, rule, event):
            pass
    runner.alert_engine = MockAlertEngine()

    rule = AlertRule(
        id="test_rule",
        user_id="u1",
        name="test",
        pincode="110001",
        lat=28.0,
        lng=77.0,
        # Order: Zepto, then Blinkit, then Instamart
        product_urls=[
            "https://zeptonow.com/product/1",
            "https://blinkit.com/product/1",
            "https://instamart.in/product/1"
        ]
    )
    
    # (Removed store_cache reassignment)

    await runner.run_rule(rule)
    
    # If they were executed concurrently, the tracker would likely have them out of order
    # or interleaved. Because they are sequential, they should exactly match:
    assert event_tracker == ["zepto", "blinkit", "instamart"]
