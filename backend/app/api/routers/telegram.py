"""
Telegram router — configure bot, manage recipients, send test messages.

Bot token is stored server-side in user_settings.json (never exposed to frontend).
Recipients (chat IDs) are managed here.
"""
import json
import httpx
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.notifications.telegram import get_bot_token, get_configured_recipients

router = APIRouter()


# ─── Pydantic models ──────────────────────────────────────────────────────────

class TelegramRecipient(BaseModel):
    id: str
    name: str
    type: str = "private"


class TelegramBotConfigRequest(BaseModel):
    bot_token: str


class TelegramBotStatusResponse(BaseModel):
    configured: bool
    bot_username: Optional[str] = None
    bot_name: Optional[str] = None


class TelegramConnectRequest(BaseModel):
    chat_id: str
    name: str = "Recipient"
    type: str = "private"


class TelegramStatusResponse(BaseModel):
    connected: bool
    bot_configured: bool
    recipients: List[TelegramRecipient]


class TelegramTestRequest(BaseModel):
    chat_id: str


# ─── User settings helpers ────────────────────────────────────────────────────

def _load_settings() -> dict:
    settings_file = get_settings().data_dir / "user_settings.json"
    if settings_file.exists():
        try:
            return json.loads(settings_file.read_text())
        except Exception:
            pass
    return {}


def _save_settings(data: dict) -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings.data_dir / "user_settings.json"
    settings_file.write_text(json.dumps(data, indent=2))


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/status", response_model=TelegramStatusResponse)
def get_telegram_status():
    """Returns whether a bot token is configured and the list of recipients."""
    token = get_bot_token()
    recipients = get_configured_recipients()
    return TelegramStatusResponse(
        connected=len(recipients) > 0,
        bot_configured=bool(token),
        recipients=[TelegramRecipient(**r) for r in recipients],
    )


@router.post("/bot/configure")
async def configure_bot(req: TelegramBotConfigRequest):
    """
    Securely store the bot token server-side.
    Verifies the token is valid before saving.
    """
    if not req.bot_token.strip():
        raise HTTPException(status_code=400, detail="Bot token cannot be empty")

    # Verify token with Telegram
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"https://api.telegram.org/bot{req.bot_token}/getMe"
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid bot token: Telegram API returned {resp.status_code}",
                )
            bot_info = resp.json().get("result", {})
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not reach Telegram API: {e}")

    # Save token to user_settings.json
    data = _load_settings()
    data["telegram_bot_token"] = req.bot_token
    _save_settings(data)

    return {
        "success": True,
        "bot_username": bot_info.get("username"),
        "bot_name": bot_info.get("first_name"),
    }


@router.get("/bot/status", response_model=TelegramBotStatusResponse)
async def get_bot_status():
    """Check if bot token is configured and valid."""
    token = get_bot_token()
    if not token:
        return TelegramBotStatusResponse(configured=False)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            if resp.status_code == 200:
                info = resp.json().get("result", {})
                return TelegramBotStatusResponse(
                    configured=True,
                    bot_username=info.get("username"),
                    bot_name=info.get("first_name"),
                )
        except Exception:
            pass

    return TelegramBotStatusResponse(configured=True)  # Token exists but couldn't verify


@router.delete("/bot")
def remove_bot():
    """Remove the stored bot token."""
    data = _load_settings()
    data.pop("telegram_bot_token", None)
    _save_settings(data)
    return {"success": True}


@router.post("/connect", response_model=TelegramStatusResponse)
def connect_recipient(req: TelegramConnectRequest):
    """Add a new Telegram chat ID as a notification recipient."""
    data = _load_settings()
    recipients: List[dict] = data.get("telegram_recipients", [])

    if not any(r["id"] == req.chat_id for r in recipients):
        recipients.append({"id": req.chat_id, "name": req.name, "type": req.type})
        data["telegram_recipients"] = recipients
        _save_settings(data)

    token = get_bot_token()
    return TelegramStatusResponse(
        connected=len(recipients) > 0,
        bot_configured=bool(token),
        recipients=[TelegramRecipient(**r) for r in recipients],
    )


@router.delete("/connect/{chat_id}", response_model=TelegramStatusResponse)
def disconnect_recipient(chat_id: str):
    """Remove a Telegram recipient."""
    data = _load_settings()
    recipients = [r for r in data.get("telegram_recipients", []) if r["id"] != chat_id]
    data["telegram_recipients"] = recipients
    _save_settings(data)

    token = get_bot_token()
    return TelegramStatusResponse(
        connected=len(recipients) > 0,
        bot_configured=bool(token),
        recipients=[TelegramRecipient(**r) for r in recipients],
    )


@router.post("/test")
async def test_telegram(req: TelegramTestRequest):
    """Send a test message to the given chat ID using the configured bot."""
    token = get_bot_token()
    if not token:
        raise HTTPException(
            status_code=400,
            detail="No bot token configured. Use /api/telegram/bot/configure first.",
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "chat_id": req.chat_id,
            "text": (
                "🎯 *Worth-It — Test Message*\n\n"
                "✅ Your Telegram integration is working correctly\\.\n\n"
                "You'll receive deal alerts here when qualifying prices are found\\."
            ),
            "parse_mode": "MarkdownV2",
        }
        try:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage", json=payload
            )
            if resp.status_code == 200:
                return {"success": True, "message": "Test message sent successfully"}
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))
