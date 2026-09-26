with open("tests/test_orchestrator.py", "r") as f:
    c = f.read()

import re
c = re.sub(r'e\["event"\]', r'e.event', c)
c = re.sub(r'e\["data"\]', r'e.model_dump()["data"]', c) # Not ideal, wait, e doesn't have ["data"] anymore except if they are DealFoundEvent.
# Let's just do e.event for event_types
with open("tests/test_orchestrator.py", "w") as f:
    f.write(c)
