import pytest
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.domain.models.deal import DealCondition
from app.platforms.base import PlatformClient, StoreResolution, ProductResult
from app.domain.models.product import PlatformProduct
from app.geo.store_cache import StoreCache

class MockPlatformClient(PlatformClient):
    @property
    def platform_name(self) -> str:
        return "mock_platform"
        
    @property
    def display_name(self) -> str:
        return "Mock Platform"
        
    @property
    def supports_sweep(self) -> bool:
        return False
        
    async def aclose(self) -> None:
        pass
        
    async def resolve_share_link(self, url: str) -> str | None:
        return None
        
    async def resolve_store(self, lat: float, lng: float, product_id: str | None = None) -> StoreResolution:
        return StoreResolution(serviceable=True, store_id="mock_store")
        
    async def product_at_store(self, product_id: str, store_id: str, lat: float | None = None, lng: float | None = None) -> ProductResult:
        return ProductResult(status="not_carried")

    async def search(self, query: str, store_id: str, lat: float, lng: float) -> list[PlatformProduct]:
        if query == "protein":
            return [
                PlatformProduct(
                    external_product_id="mock_pid_1",
                    name="Whey Protein 1kg",
                    url="http://mock.url",
                    price=1000.0,
                    mrp=2000.0, # 50% discount
                    stock=True,
                    category="protein"
                ),
                PlatformProduct(
                    external_product_id="mock_pid_2",
                    name="Whey Protein 2kg",
                    url="http://mock.url",
                    price=3800.0,
                    mrp=4000.0, # 5% discount
                    stock=True,
                    category="protein"
                )
            ]
        return []

@pytest.fixture
def store_cache(tmp_path):
    c = StoreCache(tmp_path / "test_mock_orchestrator.db")
    yield c
    c.close()

@pytest.mark.asyncio
async def test_search_orchestrator_deal_filtering(store_cache):
    client = MockPlatformClient()
    condition = DealCondition(max_price=2000.0)
    
    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=12.9716,
        center_lng=77.5946,
        local_store_id="mock_store"
    )
    
    events = []
    async for event in orchestrator.run_combined_search(
        search_id="test_1",
        keyword="protein",
        product_urls=[],
        condition=condition
    ):
        events.append(event)
        
    deal_events = [e for e in events if e.event == "deal_found"]
    assert len(deal_events) == 1
    
    deal = getattr(deal_events[0], "deal_data", None)
    assert deal["product"]["name"] == "Whey Protein 1kg"

@pytest.mark.asyncio
async def test_search_orchestrator_no_deals(store_cache):
    client = MockPlatformClient()
    condition = DealCondition(max_price=500.0) # Neither product is under 500
    
    orchestrator = DealSearchOrchestrator(
        client=client,
        store_cache=store_cache,
        center_lat=12.9716,
        center_lng=77.5946,
        local_store_id="mock_store"
    )
    
    events = []
    async for event in orchestrator.run_combined_search(
        search_id="test_2",
        keyword="protein",
        product_urls=[],
        condition=condition
    ):
        events.append(event)
        
    deal_events = [e for e in events if e.event == "deal_found"]
    assert len(deal_events) == 0
