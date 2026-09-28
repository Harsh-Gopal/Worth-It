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
from app.persistence.database import Database
from app.persistence.repositories.settings_repo import SettingsRepository

log = logging.getLogger("telegram_provider")


def _load_user_settings() -> dict:
    try:
        from app.config import get_settings
        db = Database(get_settings().database_path)
        repo = SettingsRepository(db)
        return repo.get_user_settings()
    except Exception as e:
        log.error("Failed to read user settings from DB: %s", e)
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
        configured = get_configured_recipients()
        modes = {r["id"]: r.get("notification_mode", "detailed") for r in configured}
        
        if recipient_ids:
            chat_ids = recipient_ids
        else:
            chat_ids = [r["id"] for r in configured]

        if not chat_ids:
            return NotificationResult(
                success=False,
                provider="telegram",
                error_message="No Telegram recipients configured.",
            )

        from app.notifications.telegram_formatter import format_telegram_deal_alert
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        errors = []
        overall_success = True

        for chat_id in chat_ids:
            mode = modes.get(chat_id, "detailed")
            message = format_telegram_deal_alert(event, mode=mode)
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
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
        # Re-routed to the new centralized HTML formatter
        from app.notifications.telegram_formatter import format_telegram_deal_alert
        return format_telegram_deal_alert(event)
