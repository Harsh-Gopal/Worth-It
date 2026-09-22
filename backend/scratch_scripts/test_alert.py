import json
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.api.schemas import AlertRuleCreate, AlertRuleResponse

db = Database("sqlite:///test.db")
db._init_db()
repo = AlertRepository(db)

rule_in = AlertRuleCreate(
    name="Test",
    pincode="800014",
    lat=25.60,
    lng=85.08,
)
from app.domain.models.alert import AlertRule
from datetime import datetime, timezone
import uuid

now = datetime.now(timezone.utc)
rule = AlertRule(
    id=str(uuid.uuid4()),
    name=rule_in.name,
    pincode=rule_in.pincode,
    lat=rule_in.lat,
    lng=rule_in.lng,
)
saved = repo.save_rule(rule)

rules = repo.get_all_rules()
response = AlertRuleResponse(**rules[0].model_dump())
print("Response:", response.model_dump())
