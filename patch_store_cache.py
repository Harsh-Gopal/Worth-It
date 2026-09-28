import re

with open("backend/app/geo/store_cache.py", "r") as f:
    content = f.read()

content = content.replace("import sqlite3", "import sqlite3\nfrom app.persistence.pg_wrapper import is_postgres_configured, get_postgres_connection")

init_method = """    def __init__(self, path: Path | str):
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
            
        if is_postgres_configured():
            self._db = get_postgres_connection()
        else:
            self._db = sqlite3.connect(str(path), timeout=30.0, check_same_thread=False)
            self._db.execute("PRAGMA busy_timeout=30000")
            self._db.execute("PRAGMA journal_mode=WAL")
            
        self._db.executescript(SCHEMA)
        self._lock = threading.Lock()

        self._migrate_schema()
        self._heal_corrupted_coordinates()"""

content = re.sub(r"    def __init__\(self, path: Path \| str\):.*?self\._heal_corrupted_coordinates\(\)", init_method, content, flags=re.DOTALL)

with open("backend/app/geo/store_cache.py", "w") as f:
    f.write(content)
