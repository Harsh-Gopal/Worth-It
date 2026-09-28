import re

with open("backend/app/persistence/pg_wrapper.py", "r") as f:
    content = f.read()

app_settings_query = """        elif "INSERT OR REPLACE INTO app_settings" in pg_query:
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            pg_query += \"\"\" ON CONFLICT (key) DO UPDATE SET 
                value_json=EXCLUDED.value_json, updated_at=EXCLUDED.updated_at
            \"\"\"
"""

if "app_settings" not in content:
    content = content.replace('elif "INSERT OR REPLACE INTO alert_events" in pg_query:', app_settings_query + '        elif "INSERT OR REPLACE INTO alert_events" in pg_query:')

with open("backend/app/persistence/pg_wrapper.py", "w") as f:
    f.write(content)
