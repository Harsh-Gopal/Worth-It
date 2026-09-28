import json
from datetime import datetime, timezone
from app.persistence.database import Database

class SettingsRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_setting(self, key: str, default=None):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT value_json FROM app_settings WHERE key = ?", (key,)).fetchone()
            if row:
                return json.loads(row["value_json"])
            return default

    def set_setting(self, key: str, value: any):
        with self.db.get_connection() as conn:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT OR REPLACE INTO app_settings (key, value_json, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), now)
            )
            conn.commit()

    def get_user_settings(self):
        return self.get_setting("user_settings", {})

    def save_user_settings(self, settings: dict):
        self.set_setting("user_settings", settings)
