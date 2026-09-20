import re

with open("app/domain/services/search_orchestrator.py", "r") as f:
    content = f.read()

# 1. Fix imports
content = re.sub(r'from app\.geo\.hex_grid import HexGridGenerator', 'from app.grid import hex_grid', content)
content = re.sub(r'from app\.geo\.store_discovery import StoreDiscoveryService\n', '', content)
content = re.sub(r'from app\.platforms\.instamart\.client import search, product_at_store\n', '', content)

# 2. Fix HexGridGenerator usage
content = re.sub(r'generator = HexGridGenerator\.generate\([^)]+\)\n\s*probes = generator\.generate\(\)', 'probes = hex_grid(center_lat, center_lng, radius_km, spacing_km=1.5)', content)
content = re.sub(r'probes = HexGridGenerator\.generate\(center_lat, center_lng, radius_km, spacing_km=1.5\)', 'probes = hex_grid(center_lat, center_lng, radius_km, spacing_km=1.5)', content)

# 3. Add _async_search_store if missing
if "_async_search_store" not in content:
    async_methods = """
    async def _async_search_store(self, store_id: str, query: str) -> List[InstamartProduct]:
        async with self.product_check_sem:
            if hasattr(self.client, "search"):
                results = await self.client.search(query, store_id, self.center_lat, self.center_lng)
                out = []
                for res in results:
                    out.append(InstamartProduct(
                        external_product_id=res.external_product_id,
                        name=res.name,
                        url=None,
                        price=res.price,
                        mrp=res.mrp,
                        stock=True,
                        image_url=res.image_url,
                        canonical_product_id=None
                    ))
                return out
            return []

    async def _async_product_at_store(self, store_id: str, product_id: str) -> Optional[InstamartProduct]:
        async with self.product_check_sem:
            if hasattr(self.client, "product_at_store"):
                res = await self.client.product_at_store(product_id, store_id, self.center_lat, self.center_lng)
                if not res: return None
                return InstamartProduct(
                    external_product_id=res.external_product_id,
                    name=res.name,
                    url=None,
                    price=res.price,
                    mrp=res.mrp,
                    stock=True,
                    image_url=res.image_url,
                    canonical_product_id=None
                )
            return None
            
    async def _async_discover_store(self, lat: float, lng: float):
        async with self.discovery_sem:
            try:
                res = await self.client.resolve_store(lat, lng)
                if res and res.store_id:
                    from dataclasses import dataclass
                    @dataclass
                    class _DiscoveredStore:
                        store_id: str
                        store_name: str
                        probe_lat: float
                        probe_lng: float
                    return _DiscoveredStore(store_id=res.store_id, store_name=res.store_name, probe_lat=lat, probe_lng=lng)
                return None
            except Exception as e:
                return None
"""
    content = content.replace("    # Helper to process products", async_methods + "\n    # Helper to process products")

# 4. Replace external_store_id with store_id
content = content.replace("discovered_store.external_store_id", "discovered_store.store_id")

with open("app/domain/services/search_orchestrator.py", "w") as f:
    f.write(content)
