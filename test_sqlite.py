import sqlite3
conn = sqlite3.connect(':memory:')
conn.execute("CREATE TABLE test (triggered_at TEXT)")
conn.execute("INSERT INTO test VALUES ('2026-09-28T16:59:00+00:00')")
conn.execute("INSERT INTO test VALUES ('2026-09-19T16:59:00+00:00')")
conn.execute("DELETE FROM test WHERE triggered_at < '2026-09-20T18:30:00+00:00'")
print(conn.execute("SELECT * FROM test").fetchall())
