import asyncio
from datetime import datetime, timezone, timedelta
from app.config import get_settings
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository

settings = get_settings()
db = Database(settings.database_path)
repo = AlertRepository(db)
rules = repo.get_active_rules()
now = datetime.now(timezone.utc)

for rule in rules:
    print(f"Rule {rule.id}: interval={rule.run_interval_minutes} updated_at={rule.updated_at}")
    updated_at_tz = rule.updated_at
    if updated_at_tz.tzinfo is None:
        updated_at_tz = updated_at_tz.replace(tzinfo=timezone.utc)
    
    elapsed_minutes = (now - updated_at_tz).total_seconds() / 60
    print(f"Elapsed: {elapsed_minutes} minutes")
    interval = max(rule.run_interval_minutes or 5, 5)
    if elapsed_minutes >= interval:
        print("=> THIS WOULD RUN!")
    else:
        print("=> NOT RUNNING")
