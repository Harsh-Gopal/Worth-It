"""
Telegram notification provider.

Bot token is read from:
  1. user_settings.json (data_dir/user_settings.json) — set via /api/telegram/bot/configure
  2. TELEGRAM_BOT_TOKEN env var (fallback)

Recipients are resolved in priority order:
  1. `recipient_ids` argument (per-alert override)
  2. telegram_recipients in user_settings.json
  3. TELEGRAM_CHAT_ID env var (legacy fallback)
"""
import os
import json
import logging
from typing import List, Optional

import httpx

from app.domain.models.alert import AlertEvent, NotificationResult
from app.notifications.provider import NotificationProvider

log = logging.getLogger("telegram_provider")


def _load_user_settings() -> dict:
    try:
        from app.config import get_settings
        settings_file = get_settings().data_dir / "user_settings.json"
        if settings_file.exists():
            return json.loads(settings_file.read_text())
    except Exception as e:
        log.error("Failed to read user_settings.json: %s", e)
    return {}


def get_bot_token() -> Optional[str]:
    """Read bot token from user settings, falling back to env var."""
    data = _load_user_settings()
    return data.get("telegram_bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")


def get_configured_recipients() -> List[dict]:
    """Return the globally configured Telegram recipients."""
    data = _load_user_settings()
    recipients = data.get("telegram_recipients", [])
    if recipients:
        return recipients
    # Legacy env fallback
    env_id = os.getenv("TELEGRAM_CHAT_ID")
    if env_id:
        return [{"id": env_id, "name": "Default", "type": "private"}]
    return []


class TelegramNotificationProvider(NotificationProvider):
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def send_alert(
        self,
        event: AlertEvent,
        recipient_ids: Optional[List[str]] = None,
    ) -> NotificationResult:
        token = get_bot_token()
        if not token:
            return NotificationResult(
                success=True,
                provider="telegram",
                error_message="Telegram bot token not configured — notification mocked",
            )

        # Resolve recipients
        if recipient_ids:
            chat_ids = recipient_ids
        else:
            configured = get_configured_recipients()
            chat_ids = [r["id"] for r in configured]

        if not chat_ids:
            return NotificationResult(
                success=False,
                provider="telegram",
                error_message="No Telegram recipients configured.",
            )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        message = self._format_message(event)
        errors = []
        overall_success = True

        for chat_id in chat_ids:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            }
            try:
                resp = await self.client.post(url, json=payload, timeout=10.0)
                if resp.status_code != 200:
                    overall_success = False
                    errors.append(f"{chat_id}: HTTP {resp.status_code} — {resp.text[:200]}")
            except httpx.RequestError as e:
                overall_success = False
                errors.append(f"{chat_id}: {e}")

        if overall_success:
            return NotificationResult(success=True, provider="telegram")
        return NotificationResult(
            success=False,
            provider="telegram",
            error_message="; ".join(errors),
            retryable=True,
        )

    def _format_message(self, event: AlertEvent) -> str:
        product_name = event.product_name or event.instamart_product_id
        lines = [
            "🔍 *WORTH-IT*",
            "",
            f"*{product_name}*",
            "",
        ]

        # Pricing
        if event.mrp and event.mrp > event.price:
            lines.append(f"💰 ₹{event.price:.0f}  ~~₹{event.mrp:.0f}~~")
        else:
            lines.append(f"💰 ₹{event.price:.0f}")

        lines.append(f"🔥 *{event.discount_percent:.0f}% OFF*")

        if event.is_historical_low if hasattr(event, "is_historical_low") else False:
            lines.append("📉 *Historical Low Price!*")

        if event.previous_price and event.price_drop_percent:
            lines.append(f"📊 Dropped {event.price_drop_percent:.1f}% from ₹{event.previous_price:.0f}")

        lines.append("")

        # Location
        if event.store_name:
            lines.append(f"📍 {event.store_name}")
        else:
            lines.append(f"🏪 Store: `{event.store_id}`")

        if event.distance_km is not None:
            lines.append(f"📏 {event.distance_km:.1f} km away")

        lines.append("")
        lines.append(f"_Why: {event.trigger_reason}_")
        lines.append("")

        # Link
        product_url = event.product_url or f"https://www.swiggy.com/instamart/item/{event.instamart_product_id}"
        lines.append(f"[🛒 Open on Instamart]({product_url})")

        return "\n".join(lines)
