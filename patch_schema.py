import re

with open("backend/app/persistence/database.py", "r") as f:
    content = f.read()

new_schema = """-- App Settings
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

if "app_settings" not in content:
    content = content.replace("CREATE TABLE IF NOT EXISTS alert_rules", new_schema + "\n-- Alert Rules\nCREATE TABLE IF NOT EXISTS alert_rules")

with open("backend/app/persistence/database.py", "w") as f:
    f.write(content)
