with open("tests/integration/test_alert_e2e.py", "r") as f:
    c = f.read()

# Replace the closing dict `}` of yield DealFoundEvent
# There are two mock functions in the test file.
import re

c = re.sub(
    r'(yield DealFoundEvent\([^}]+\}\n            \}\n        )(\})',
    r'\1)',
    c
)

with open("tests/integration/test_alert_e2e.py", "w") as f:
    f.write(c)
