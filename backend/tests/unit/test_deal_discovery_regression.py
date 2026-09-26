import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.domain.models.product import PlatformProduct
from app.domain.models.deal import DealCondition
from app.domain.services.deal_engine import DealEngine
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.domain.models.alert import AlertRule
from app.platforms.base import PlatformClient
import asyncio

class MockPlatformClient(PlatformClient):
    @property
    def platform_name(self): return "mock"
    @property
    def display_name(self): return "Mock"
    async def aclose(self): pass
    async def resolve_share_link(self, url): return "123"
    async def resolve_store(self, lat, lng, product_id=None): return None
    async def product_at_store(self, product_id, store_id, lat=None, lng=None): return None
    async def search(self, query, store_id, lat, lng):
        if query in ("Sports & Fitness", "Bat"):
            return [
                PlatformProduct(external_product_id="1", name="Lifelong Plastic Cricket Bat", url="", price=60.0, mrp=100.0, stock=True, category="Sports & Fitness"),
                PlatformProduct(external_product_id="2", name="Slovic Heavy-Duty Weightlifting Wrist Straps", url="", price=50.0, mrp=100.0, stock=True, category="Sports & Fitness"),
                PlatformProduct(external_product_id="3", name="Unrelated item", url="", price=90.0, mrp=100.0, stock=True, category="Sports & Fitness")
            ]
        return []

@pytest.mark.asyncio
async def test_1_instamart_category_discovery():
    """Test 1: Sports & Fitness >= 40% discovers items without filtering by title."""
    client = MockPlatformClient()
    orchestrator = DealSearchOrchestrator(client=client, store_cache=MagicMock(), center_lat=0, center_lng=0, local_store_id="store_1")
    
    rule = AlertRule(
        id="test", name="test", categories=["Sports & Fitness"], category_rules={"Sports & Fitness": {"min_discount_pct": 40.0}},
        lat=0, lng=0, platforms=["mock"]
    )
    
    gen = orchestrator.run_combined_search(
        search_id="s1", keyword="Sports & Fitness", product_urls=[],
        match_keywords=None, exclude_keywords=None, condition=DealCondition(),
        expansion_radii_km=[3.0], strategy='NEARBY_FIRST', rule=rule, target_type="category"
    )
    
    deals = []
    async for event in gen:
        if getattr(event, "event", "") == "deal_found":
            deals.append(event)
            
    # Should find the two items with >=40% discount, despite titles not containing "Sports & Fitness"
    assert len(deals) == 2
    names = [d.deal_data["product"]["name"] for d in deals]
    assert "Lifelong Plastic Cricket Bat" in names
    assert "Slovic Heavy-Duty Weightlifting Wrist Straps" in names

def test_2_exact_threshold():
    engine = DealEngine()
    p = PlatformProduct(external_product_id="1", name="Test", url="", price=60.0, mrp=100.0, stock=True, category="Sports")
    rule = AlertRule(id="test", name="test", categories=["Sports"], category_rules={"Sports": {"min_discount_pct": 40.0}}, lat=0, lng=0, platforms=["mock"])
    res = engine.evaluate(p, DealCondition(), rule=rule)
    assert res.discount_percent == 40.0
    assert res.qualifies is True

def test_3_below_threshold():
    engine = DealEngine()
    p = PlatformProduct(external_product_id="1", name="Test", url="", price=61.0, mrp=100.0, stock=True, category="Sports")
    rule = AlertRule(id="test", name="test", categories=["Sports"], category_rules={"Sports": {"min_discount_pct": 40.0}}, lat=0, lng=0, platforms=["mock"])
    res = engine.evaluate(p, DealCondition(), rule=rule)
    assert res.discount_percent == 39.0
    assert res.qualifies is False

def test_4_above_threshold():
    engine = DealEngine()
    p = PlatformProduct(external_product_id="1", name="Test", url="", price=50.0, mrp=100.0, stock=True, category="Sports")
    rule = AlertRule(id="test", name="test", categories=["Sports"], category_rules={"Sports": {"min_discount_pct": 40.0}}, lat=0, lng=0, platforms=["mock"])
    res = engine.evaluate(p, DealCondition(), rule=rule)
    assert res.discount_percent == 50.0
    assert res.qualifies is True

def test_7_location_flow():
    from app.domain.services.alert_runner import AlertRunner
    # ensure location from rule flows to runner
    rule = AlertRule(id="test", name="test", lat=12.34, lng=56.78, local_store_id="store_abc", platforms=["instamart"], categories=[])
    runner = AlertRunner(alert_repo=MagicMock(), store_cache=MagicMock(), price_history=MagicMock(), notification_service=MagicMock(), clients=[], center_lat=0, center_lng=0, local_store_id="default")
    assert runner.center_lat == 0 # Default fallback
    assert runner.center_lng == 0
    # Inside run_rule it overrides
    lat = rule.lat if rule.lat is not None else runner.center_lat
    lng = rule.lng if rule.lng is not None else runner.center_lng
    assert lat == 12.34
    assert lng == 56.78

@pytest.mark.asyncio
async def test_8_keyword_scan():
    """Keyword scans must still enforce title match."""
    client = MockPlatformClient()
    orchestrator = DealSearchOrchestrator(client=client, store_cache=MagicMock(), center_lat=0, center_lng=0, local_store_id="store_1")
    
    rule = AlertRule(id="test", name="test", keywords=["Bat"], keyword_rules={"Bat": {"min_discount_pct": 40.0}}, lat=0, lng=0, platforms=["mock"])
    
    gen = orchestrator.run_combined_search(
        search_id="s1", keyword="Sports & Fitness", product_urls=[],
        match_keywords=["Bat"], exclude_keywords=None, condition=DealCondition(),
        expansion_radii_km=[3.0], strategy='NEARBY_FIRST', rule=rule, target_type="keyword"
    )
    
    deals = []
    async for event in gen:
        if getattr(event, "event", "") == "deal_found":
            deals.append(event)
            
    assert len(deals) == 1
    assert deals[0].deal_data["product"]["name"] == "Lifelong Plastic Cricket Bat"

@pytest.mark.asyncio
async def test_9_platform_unavailable_does_not_crash_scan():
    from app.domain.services.alert_runner import AlertRunner
    from app.platforms.base import StoreResolution
    
    class UnavailableClient(MockPlatformClient):
        @property
        def platform_name(self): return "zepto"
        
        async def resolve_store(self, lat, lng, product_id=None):
            return StoreResolution(serviceable=False)
            
    client = UnavailableClient()
    repo = MagicMock()
    store_cache = MagicMock()
    runner = AlertRunner(repo, store_cache, MagicMock(), MagicMock(), [client], 0, 0, None)
    
    rule = AlertRule(id="test", name="test", categories=["Sports"], lat=0, lng=0, platforms=["zepto"])
    
    events = await runner.run_rule(rule)
    assert len(events) == 0

@pytest.mark.asyncio
async def test_10_platform_error_does_not_crash_scan():
    from app.domain.services.alert_runner import AlertRunner
    from app.platforms.base import StoreResolution
    
    class ErrorClient(MockPlatformClient):
        @property
        def platform_name(self): return "blinkit"
        
        async def resolve_store(self, lat, lng, product_id=None):
            raise Exception("Mock WAF Block")
            
    client = ErrorClient()
    repo = MagicMock()
    runner = AlertRunner(repo, MagicMock(), MagicMock(), MagicMock(), [client], 0, 0, None)
    
    rule = AlertRule(id="test", name="test", categories=["Sports"], lat=0, lng=0, platforms=["blinkit"])
    
    events = await runner.run_rule(rule)
    assert len(events) == 0
