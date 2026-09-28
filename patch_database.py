import re

with open("backend/app/persistence/database.py", "r") as f:
    content = f.read()

content = content.replace("import sqlite3", "import sqlite3\nfrom .pg_wrapper import is_postgres_configured, get_postgres_connection")

get_conn_method = """    @contextmanager
    def get_connection(self):
        if is_postgres_configured():
            conn = get_postgres_connection()
            try:
                with conn:
                    yield conn
            finally:
                conn.close()
            return

        conn = sqlite3.connect(str(self.path), timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=30000")
            # Using 'with conn' ensures auto-commit on success and rollback on failure
            with conn:
                yield conn
        finally:
            conn.close()"""

content = re.sub(r"    @contextmanager\n    def get_connection\(self\):.*?finally:\n            conn\.close\(\)", get_conn_method, content, flags=re.DOTALL)

with open("backend/app/persistence/database.py", "w") as f:
    f.write(content)
