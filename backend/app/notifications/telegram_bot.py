import asyncio
import httpx
import logging
import json
from typing import Optional
from app.notifications.telegram import get_bot_token, get_configured_recipients
from app.config import get_settings
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.domain.models.alert import AlertRule
from datetime import datetime, timezone
from app.api.routers.location import _nom_forward, _resolve_store_id

log = logging.getLogger("telegram_bot")

async def start_telegram_bot_polling():
    token = get_bot_token()
    if not token:
        log.info("Telegram Bot token not configured. Skipping bot polling.")
        return

    offset = 0
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                resp = await client.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        await process_telegram_update(update, client, token)
            except asyncio.CancelledError:
                log.info("Telegram bot polling stopped.")
                break
            except Exception as e:
                log.warning(f"Telegram bot polling error: {e}")
                await asyncio.sleep(5)
            
            await asyncio.sleep(1)

def _get_user_rule_id(chat_id: str) -> str:
    # Use the same shared state as the web application for the single-user mode
    return "primary_monitor"

async def _send_message(client: httpx.AsyncClient, token: str, chat_id: str, text: str, reply_markup: dict = None, parse_mode: str = "HTML"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)
    except Exception as e:
        log.error(f"Failed to send message: {e}")

async def process_telegram_update(update: dict, client: httpx.AsyncClient, token: str):
    message = update.get("message")
    if not message:
        return
    
    text = message.get("text", "")
    chat_id = str(message.get("chat", {}).get("id"))
    if not text or not chat_id:
        return

    settings = get_settings()
    db = Database(settings.database_path)
    repo = AlertRepository(db)
    rule_id = _get_user_rule_id(chat_id)

    # Automatically ensure rule exists
    rule = repo.get_rule(rule_id)
    if not rule:
        now = datetime.now(timezone.utc)
        rule = AlertRule(
            id=rule_id,
            name=f"Telegram {chat_id}",
            lat=settings.center_lat,
            lng=settings.center_lng,
            created_at=now,
            updated_at=now,
            telegram_recipient_ids=[chat_id]
        )
        repo.save_rule(rule)
        
        # Ensure user is in user_settings.json
        user_settings_path = settings.data_dir / "user_settings.json"
        if user_settings_path.exists():
            try:
                data = json.loads(user_settings_path.read_text())
            except Exception:
                data = {}
        else:
            data = {}
        
        recipients = data.get("telegram_recipients", [])
        if not any(r["id"] == chat_id for r in recipients):
            recipients.append({
                "id": chat_id,
                "name": message.get("chat", {}).get("first_name", "User"),
                "type": "private",
                "notification_mode": "detailed"
            })
            data["telegram_recipients"] = recipients
            user_settings_path.write_text(json.dumps(data, indent=2))

    cmd = text.split(" ")[0].lower()
    args = text.split(" ")[1:]

    # Parse commands
    if cmd == "/start":
        import os
        webapp_url = os.environ.get("WORTH_IT_WEB_URL", os.environ.get("TELEGRAM_WEBAPP_URL", ""))
        reply_markup = None
        if webapp_url:
            reply_markup = {
                "inline_keyboard": [[{
                    "text": "🛒 Open Worth-It",
                    "web_app": {"url": webapp_url}
                }]]
            }
        msg = "Welcome to Worth-It! I will track price drops for you.\nUse /help to see all commands."
        await _send_message(client, token, chat_id, msg, reply_markup=reply_markup)
    
    elif cmd == "/help":
        msg = (
            "<b>Worth-It Bot Commands</b>\n\n"
            "/start - Set up Worth-It\n"
            "/status - View current tracking status\n"
            "/scan - Trigger a scan immediately\n"
            "/pause - Pause tracking\n"
            "/resume - Resume tracking\n"
            "/wishlist - View tracked wishlist products\n"
            "/add [url] - Add product to wishlist\n"
            "/remove [index] - Remove wishlist product\n"
            "/targets - View tracking keywords\n"
            "/addtarget [keyword] - Add tracking keyword\n"
            "/removetarget [keyword] - Remove tracking keyword\n"
            "/notifications - Change Simple/Detailed notification mode\n"
            "/location [pincode] - Set 6-digit Indian PINCODE\n"
            "/frequency [minutes] - Set scan frequency\n"
            "/test - Send a test notification"
        )
        await _send_message(client, token, chat_id, msg)
    
    elif cmd == "/status":
        has_target = bool(rule.keywords or rule.categories or rule.product_urls)
        is_active = rule.enabled and has_target

        msg_lines = ["<b>Worth-It Status</b>", ""]
        if is_active:
            msg_lines.append("Tracking: Active")
        elif rule.enabled and not has_target:
            msg_lines.append("Tracking: Not running")
            msg_lines.append("Reason: No tracking targets configured")
            msg_lines.append("")
        else:
            msg_lines.append("Tracking: Paused")

        msg_lines.append(f"Frequency: Every {rule.run_interval_minutes or 30} mins")
        msg_lines.append(f"Wishlist: {len(rule.product_urls or [])} products")
        msg_lines.append(f"Keywords: {len(rule.keywords or [])}")
        
        if rule.pincode:
            msg_lines.append(f"Pincode: {rule.pincode}")

        # Determine notification mode
        mode = "Detailed"
        user_settings_path = settings.data_dir / "user_settings.json"
        if user_settings_path.exists():
            try:
                dt = json.loads(user_settings_path.read_text())
                for r in dt.get("telegram_recipients", []):
                    if r["id"] == chat_id:
                        mode = r.get("notification_mode", "detailed").title()
                        break
            except Exception:
                pass
        msg_lines.append(f"Notifications: {mode}")

        await _send_message(client, token, chat_id, "\n".join(msg_lines))
    
    elif cmd == "/pause":
        rule.enabled = False
        repo.save_rule(rule)
        await _send_message(client, token, chat_id, f"Tracking paused.\n\nFrequency: Every {rule.run_interval_minutes or 30} mins\nTargets: {len(rule.keywords)}")
    
    elif cmd == "/resume":
        has_target = bool(rule.keywords or rule.categories or rule.product_urls)
        if not has_target:
            await _send_message(client, token, chat_id, "Tracking cannot start yet.\n\nReason: No tracking targets configured.\n\nAdd a target using:\n/addtarget [keyword]")
        else:
            rule.enabled = True
            repo.save_rule(rule)
            await _send_message(client, token, chat_id, f"Tracking resumed.\n\nFrequency: Every {rule.run_interval_minutes or 30} mins\nTargets: {len(rule.keywords)}")
        
    elif cmd == "/wishlist":
        if not rule.product_urls:
            await _send_message(client, token, chat_id, "Your wishlist is empty.")
        else:
            msg = f"<b>Your Wishlist ({len(rule.product_urls)})</b>\n\n"
            for i, url in enumerate(rule.product_urls):
                # Try to get latest event for metadata
                with repo.db.get_connection() as conn:
                    row = conn.execute("SELECT product_name, platform, price FROM alert_events WHERE alert_rule_id = ? AND product_url = ? ORDER BY triggered_at DESC LIMIT 1", (rule_id, url)).fetchone()
                    if row:
                        msg += f"{i+1}. {row['product_name']}\n   Platform: {row['platform'].title()}\n   Price: ₹{row['price']}\n   URL: {url}\n\n"
                    else:
                        msg += f"{i+1}. {url}\n\n"
            await _send_message(client, token, chat_id, msg.strip())
            
    elif cmd == "/add":
        if not args:
            await _send_message(client, token, chat_id, "Please provide a URL: /add https://instamart...")
            return
        url = " ".join(args)
        if url not in rule.product_urls:
            rule.product_urls.append(url)
            repo.save_rule(rule)
        await _send_message(client, token, chat_id, "Added to wishlist!")
        
    elif cmd == "/remove":
        if not args or not args[0].isdigit():
            await _send_message(client, token, chat_id, "Please provide an index: /remove 1")
            return
        idx = int(args[0]) - 1
        if 0 <= idx < len(rule.product_urls):
            removed = rule.product_urls.pop(idx)
            repo.save_rule(rule)
            await _send_message(client, token, chat_id, f"Removed item from wishlist.")
        else:
            await _send_message(client, token, chat_id, "Invalid index.")

    elif cmd == "/targets":
        if not rule.keywords:
            await _send_message(client, token, chat_id, "No tracking targets configured.")
        else:
            msg = "<b>Tracking Targets</b>\n\n" + "\n".join(f"{i+1}. {k}" for i, k in enumerate(rule.keywords))
            await _send_message(client, token, chat_id, msg)
            
    elif cmd == "/addtarget":
        if not args:
            await _send_message(client, token, chat_id, "Please provide a keyword: /addtarget milk")
            return
        kw = " ".join(args)
        if kw not in rule.keywords:
            rule.keywords.append(kw)
            repo.save_rule(rule)
        await _send_message(client, token, chat_id, f"Target added:\n{kw}\n\nTotal targets: {len(rule.keywords)}")
        
    elif cmd == "/removetarget":
        if not args:
            await _send_message(client, token, chat_id, "Please provide a keyword: /removetarget milk")
            return
        kw = " ".join(args)
        if kw in rule.keywords:
            rule.keywords.remove(kw)
            repo.save_rule(rule)
            await _send_message(client, token, chat_id, f"Removed target: {kw}")
        else:
            await _send_message(client, token, chat_id, "Target not found.")
            
    elif cmd == "/notifications":
        # Toggle simple/detailed mode
        user_settings_path = settings.data_dir / "user_settings.json"
        data = json.loads(user_settings_path.read_text())
        recipients = data.get("telegram_recipients", [])
        for r in recipients:
            if r["id"] == chat_id:
                curr = r.get("notification_mode", "detailed")
                new_mode = "simple" if curr == "detailed" else "detailed"
                r["notification_mode"] = new_mode
                data["telegram_recipients"] = recipients
                user_settings_path.write_text(json.dumps(data, indent=2))
                await _send_message(client, token, chat_id, f"Notification mode set to <b>{new_mode.upper()}</b>")
                break
                
    elif cmd == "/location":
        if not args:
            await _send_message(client, token, chat_id, "Invalid pincode.\n\nPlease provide a valid 6-digit Indian PINCODE.\n\nExample:\n/location 800014")
            return
        pincode = args[0]
        if len(pincode) == 6 and pincode.isdigit():
            # Geocode the pincode to get lat/lng
            try:
                items = await _nom_forward(pincode, limit=1)
                if items:
                    lat = float(items[0]["lat"])
                    lng = float(items[0]["lon"])
                    local_store_id = await _resolve_store_id(lat, lng)
                    
                    rule.pincode = pincode
                    rule.lat = lat
                    rule.lng = lng
                    rule.local_store_id = local_store_id
                    repo.save_rule(rule)
                    
                    display_name = items[0].get("display_name", "")
                    # Extract the first segment before the comma as a rough area name if available
                    area = display_name.split(",")[0] if display_name else ""
                    
                    response_msg = f"Location updated successfully.\n\nPincode: {pincode}"
                    if area and area != pincode:
                        response_msg += f"\nArea: {area}"
                    response_msg += "\n\nThis location will be used for future scans."
                    
                    await _send_message(client, token, chat_id, response_msg)
                else:
                    await _send_message(client, token, chat_id, "Could not resolve that pincode. Please try another one.")
            except Exception as e:
                log.error(f"Telegram /location geocode failed: {e}")
                await _send_message(client, token, chat_id, "Failed to resolve pincode. Please try again later.")
        else:
            await _send_message(client, token, chat_id, "Invalid pincode.\n\nPlease provide a valid 6-digit Indian PINCODE.\n\nExample:\n/location 800014")
            
    elif cmd == "/frequency":
        if not args or not args[0].isdigit():
            await _send_message(client, token, chat_id, "Usage: /frequency [minutes]")
            return
        mins = int(args[0])
        if mins < 1:
            await _send_message(client, token, chat_id, "Frequency must be at least 1 minute.")
            return
        rule.run_interval_minutes = mins
        repo.save_rule(rule)
        await _send_message(client, token, chat_id, f"Scan frequency updated.\n\nEvery {mins} minutes.")

    elif cmd == "/scan":
        await _send_message(client, token, chat_id, "Triggering immediate scan...")
        from app.api.routers.alerts import _trigger_alert_run
        from app.geo.store_cache import get_global_cache
        from app.domain.services.price_history_service import PriceHistoryService
        from app.persistence.repositories.price_history_repo import PriceHistoryRepository
        
        has_target = bool(rule.keywords or rule.categories or rule.product_urls)
        if not has_target:
            await _send_message(client, token, chat_id, "Scan could not start.\n\nReason: No tracking targets configured.")
            return

        store_cache = get_global_cache(settings.store_cache_path)
        ph = PriceHistoryService(PriceHistoryRepository(db))
        success = _trigger_alert_run(rule_id, repo, store_cache, ph)
        if success:
            await _send_message(client, token, chat_id, "Scan started. You'll receive qualifying deal alerts when results are available.")
        else:
            await _send_message(client, token, chat_id, "Scan could not start.\n\nReason: Configuration missing.")
        
    elif cmd == "/test":
        from app.notifications.telegram_formatter import format_telegram_test_message
        msg = format_telegram_test_message()
        await _send_message(client, token, chat_id, msg)
        
    elif cmd == "/open":
        import os
        webapp_url = os.environ.get("WORTH_IT_WEB_URL", os.environ.get("TELEGRAM_WEBAPP_URL", ""))
        if webapp_url:
            reply_markup = {
                "inline_keyboard": [[{
                    "text": "🛒 Open Worth-It",
                    "web_app": {"url": webapp_url}
                }]]
            }
            await _send_message(client, token, chat_id, "Click below to open the Web App:", reply_markup=reply_markup)
        else:
            await _send_message(client, token, chat_id, "WORTH_IT_WEB_URL is not configured.")
