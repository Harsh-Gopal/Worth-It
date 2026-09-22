import asyncio
from app.config import get_settings
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository

settings = get_settings()
db = Database(settings.database_path)
repo = AlertRepository(db)
rules = repo.get_active_rules()
for r in rules:
    print(r.id, r.run_interval_minutes, r.updated_at)
