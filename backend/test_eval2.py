import asyncio
from unittest.mock import patch, MagicMock
from app.domain.models.deal import DealCondition
from app.domain.models.product import CanonicalProduct, InstamartProduct
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from app.geo.store_cache import StoreCache

async def run():
    store_cache = StoreCache(":memory:")
    
    @patch("app.domain.services.search_orchestrator.ProductDiscoveryEngine")
    @patch("app.domain.services.search_orchestrator.product_at_store")
    @patch("app.domain.services.search_orchestrator.StoreDiscoveryService")
    async def do_test(mock_store_discovery, mock_product_at_store, mock_product_discovery):
        mock_discovery_instance = MagicMock()
        mock_discovery_instance.discover.return_value = [
            CanonicalProduct(id="canonical_123", brand="Nutrabay", normalized_name="nutrabay protein", category="supplements")
        ]
        mock_product_discovery.return_value = mock_discovery_instance
        
        def mock_pas(client, store_id, ext_id):
            return InstamartProduct(external_product_id="123", name="Nutrabay Protein", url="", price=800, mrp=1000, stock=True, category="")
        mock_product_at_store.side_effect = mock_pas
        
        orchestrator = DealSearchOrchestrator(
            client=MagicMock(), store_cache=store_cache,
            center_lat=12.97, center_lng=77.59, local_store_id="store_local"
        )
        
        # Override _record_and_evaluate to see what is returned
        original_eval = orchestrator._record_and_evaluate
        def logging_eval(product, store_id, condition):
            res = original_eval(product, store_id, condition)
            print(f">>> EVAL RESULT: {res}")
            return res
        orchestrator._record_and_evaluate = logging_eval
        
        condition = DealCondition(min_discount_pct=50.0)
        async for event in orchestrator.run_search("search_1", "nutrabay protein", condition, expansion_radii_km=[3.0], strategy="NEARBY_FIRST"):
            pass

    await do_test()

asyncio.run(run())
