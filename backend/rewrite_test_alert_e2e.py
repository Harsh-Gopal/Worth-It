import re

with open("tests/integration/test_alert_e2e.py", "r") as f:
    content = f.read()

# Replace all occurrences of yield dict with yield EventObjects
new_content = re.sub(
    r'yield \{"event": "search_started"\}',
    r'from app.domain.models.events import SearchStartedEvent, DealFoundEvent, SearchCompletedEvent\n        yield SearchStartedEvent(search_id="test", keyword="test", search_mode="keyword", type="keyword")',
    content
)

new_content = re.sub(
    r'yield \{"event": "search_completed"\}',
    r'yield SearchCompletedEvent(search_id="test", message="Done", total_deals=1)',
    new_content
)

new_content = re.sub(
    r'yield \{\s*"event": "deal_found",\s*"data": \{',
    r'yield DealFoundEvent(search_id="test", deal_data={',
    new_content
)

new_content = re.sub(
    r'distance_km": 5\.0\n\s*\}\n\s*\}\n\s*\}',
    r'distance_km": 5.0\n                }\n            })',
    new_content
)

with open("tests/integration/test_alert_e2e.py", "w") as f:
    f.write(new_content)
