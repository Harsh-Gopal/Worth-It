from backend.app.domain.models.alert import AlertEvent
from backend.app.notifications.telegram_formatter import format_telegram_deal_alert
from datetime import datetime

event = AlertEvent(
    id="123",
    alert_rule_id="rule1",
    instamart_product_id="prod1",
    product_name="Test Product < > & \" '",
    store_id="store1",
    price=10.5,
    mrp=20.0,
    discount_percent=47.5,
    trigger_reason="Because it's cheap",
    triggered_at=datetime.now()
)

text = format_telegram_deal_alert(event)
print(text)
