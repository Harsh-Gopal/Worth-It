import re

with open("tests/integration/test_alert_e2e.py", "r") as f:
    c = f.read()

c = c.replace(
    'yield {"event": "search_started"}',
    'from app.domain.models.events import SearchStartedEvent, DealFoundEvent, SearchCompletedEvent\n        yield SearchStartedEvent(search_id="test", keyword="test", search_mode="keyword", type="keyword")'
)
c = c.replace(
    'yield {"event": "search_completed"}',
    'yield SearchCompletedEvent(search_id="test", message="Done", total_deals=1)'
)
c = c.replace(
    'yield {\n            "event": "deal_found",\n            "data": {',
    'yield DealFoundEvent(\n            search_id="test",\n            deal_data={'
)
# Note: we need to replace the closing brace of DealFoundEvent dict with `})`
# The easiest way is to use regex or just standard find and replace.
