from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class OrchestratorEvent(BaseModel):
    event: str
    search_id: str
    timestamp: datetime = None

    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.utcnow()

class SearchStartedEvent(OrchestratorEvent):
    event: str = "search_started"
    keyword: str
    search_mode: str
    type: str
    product_ids: List[str] = []

class LocalSearchStartedEvent(OrchestratorEvent):
    event: str = "local_search_started"
    store_id: str

class DealFoundEvent(OrchestratorEvent):
    event: str = "deal_found"
    deal_data: Dict[str, Any]

class ProductCheckFailedEvent(OrchestratorEvent):
    event: str = "product_check_failed"
    store_id: str
    product_id: str
    error: str

class LocalSearchCompletedEvent(OrchestratorEvent):
    event: str = "local_search_completed"
    store_id: str
    deals_found: int = 0

class RadiusExpansionStartedEvent(OrchestratorEvent):
    event: str = "radius_expansion_started"
    radii: List[float]

class RadiusScanStartedEvent(OrchestratorEvent):
    event: str = "radius_scan_started"
    radius_km: float

class ProbeStartedEvent(OrchestratorEvent):
    event: str = "probe_started"
    count: int

class StoreDiscoveredEvent(OrchestratorEvent):
    event: str = "store_discovered"
    store_id: str
    lat: float
    lng: float
    name: Optional[str]

class ProbeCompletedEvent(OrchestratorEvent):
    event: str = "probe_completed"

class StoreScanStartedEvent(OrchestratorEvent):
    event: str = "store_scan_started"
    stores_count: int

class ProductCheckStartedEvent(OrchestratorEvent):
    event: str = "product_check_started"
    store_id: str
    count: int

class ProductCheckCompletedEvent(OrchestratorEvent):
    event: str = "product_check_completed"
    store_id: str

class StoreScanFailedEvent(OrchestratorEvent):
    event: str = "store_scan_failed"
    store_id: str
    error: str

class RadiusCompletedEvent(OrchestratorEvent):
    event: str = "radius_completed"
    radius_km: float
    deals_found: int

class SearchCompletedEvent(OrchestratorEvent):
    event: str = "search_completed"
    message: str
    total_deals: int

class SearchCancelledEvent(OrchestratorEvent):
    event: str = "search_cancelled"
    message: str

class SearchErrorEvent(OrchestratorEvent):
    event: str = "search_error"
    message: str
    platform: Optional[str] = None
