import sqlite3
import os

db_path = "data/alerts.db"
if not os.path.exists(db_path):
    print("Database not found")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM alert_events")
    print("Count of events:", cur.fetchone()[0])
    cur.execute("SELECT triggered_at FROM alert_events ORDER BY triggered_at DESC LIMIT 5")
    for row in cur.fetchall():
        print(row)
