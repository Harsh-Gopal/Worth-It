import asyncio
from app.notifications.telegram import TelegramNotificationProvider
from app.domain.models.alert import AlertEvent
from app.domain.models.intelligence import DealLevel
from datetime import datetime, timezone
import httpx
import logging
from uuid import uuid4

logging.basicConfig(level=logging.INFO)

async def main():
    async with httpx.AsyncClient() as client:
        provider = TelegramNotificationProvider(client)
        event = AlertEvent(
            id=str(uuid4()),
            alert_rule_id="test",
            canonical_product_id="test_cp",
            instamart_product_id="test_ip",
            product_name="Test Product",
            product_url="https://blinkit.com",
            store_id="store1",
            store_name="Test Store",
            distance_km=1.2,
            price=150.0,
            mrp=200.0,
            discount_percent=25.0,
            previous_price=None,
            price_drop_percent=None,
            trigger_reason="Test reason",
            triggered_at=datetime.now(timezone.utc),
            notification_status="pending",
            notification_attempts=0,
            product_image="https://example.com/img.jpg",
            platform="blinkit",
            store_pincode="123456",
            search_pincode="123456",
            origin_lat=12.0,
            origin_lng=77.0,
            deal_level=DealLevel.NORMAL,
            deal_score=50,
            savings_amount=50.0
        )
        res = await provider.send_alert(event)
        print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
