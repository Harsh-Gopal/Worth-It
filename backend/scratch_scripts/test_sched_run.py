import asyncio
from datetime import datetime, timezone, timedelta
from app.config import get_settings
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.scheduler import _run_all_active_alerts

settings = get_settings()
db = Database(settings.database_path)
repo = AlertRepository(db)
rules = repo.get_active_rules()
now = datetime.now(timezone.utc)
for rule in rules:
    rule.updated_at = now - timedelta(minutes=10)
    repo.save_rule(rule)
    print(f"Faked updated_at for rule {rule.id}")

async def main():
    print("Running _run_all_active_alerts...")
    await _run_all_active_alerts()

asyncio.run(main())
