with open('app/domain/services/search_orchestrator.py', 'r') as f:
    content = f.read()

import_stmt = """from app.domain.models.events import *
from app.domain.models.product import CanonicalProduct, PlatformProduct

def create_event(data_dict: dict) -> OrchestratorEvent:
    event_type = data_dict.get("event")
    payload = data_dict.get("data", {})
    payload["search_id"] = data_dict.get("search_id", "")
    
    mapping = {
        "search_started": SearchStartedEvent,
        "local_search_started": LocalSearchStartedEvent,
        "deal_found": DealFoundEvent,
        "product_check_failed": ProductCheckFailedEvent,
        "local_search_completed": LocalSearchCompletedEvent,
        "radius_expansion_started": RadiusExpansionStartedEvent,
        "radius_scan_started": RadiusScanStartedEvent,
        "probe_started": ProbeStartedEvent,
        "store_discovered": StoreDiscoveredEvent,
        "probe_completed": ProbeCompletedEvent,
        "store_scan_started": StoreScanStartedEvent,
        "product_check_started": ProductCheckStartedEvent,
        "product_check_completed": ProductCheckCompletedEvent,
        "store_scan_failed": StoreScanFailedEvent,
        "radius_completed": RadiusCompletedEvent,
        "search_completed": SearchCompletedEvent,
        "search_cancelled": SearchCancelledEvent,
        "search_error": SearchErrorEvent,
        "product_discovered": OrchestratorEvent,
        "radius_started": RadiusScanStartedEvent
    }
    cls = mapping.get(event_type, OrchestratorEvent)
    
    if event_type == "deal_found":
        return DealFoundEvent(search_id=payload["search_id"], deal_data=payload)
    
    return cls(**payload, event=event_type)

"""

content = content.replace("from app.domain.models.product import CanonicalProduct, PlatformProduct", import_stmt)
content = content.replace("AsyncIterator[Dict]", "AsyncIterator[OrchestratorEvent]")

import ast

tree = ast.parse(content)

class YieldTransformer(ast.NodeTransformer):
    def visit_Yield(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.Dict):
            has_event = any(isinstance(k, ast.Constant) and k.value == "event" for k in node.value.keys)
            if has_event:
                new_node = ast.Yield(
                    value=ast.Call(
                        func=ast.Name(id='create_event', ctx=ast.Load()),
                        args=[node.value],
                        keywords=[]
                    )
                )
                return ast.copy_location(new_node, node)
        return node

transformer = YieldTransformer()
new_tree = transformer.visit(tree)
ast.fix_missing_locations(new_tree)
new_content = ast.unparse(new_tree)

with open('app/domain/services/search_orchestrator.py', 'w') as f:
    f.write(new_content)
