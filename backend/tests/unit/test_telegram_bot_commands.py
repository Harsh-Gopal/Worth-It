import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.notifications.telegram_bot import process_telegram_update
from app.domain.models.alert import AlertRule

@pytest.mark.asyncio
async def test_telegram_bot_location_valid():
    client_mock = AsyncMock()
    token = "test"
    update = {
        "message": {
            "chat": {"id": 12345},
            "text": "/location 800014",
            "date": 123456789
        }
    }
    with patch("app.notifications.telegram_bot.Database"), \
         patch("app.notifications.telegram_bot.AlertRepository") as mock_repo_class, \
         patch("app.notifications.telegram_bot._send_message", new_callable=AsyncMock) as send_mock:
        repo_mock = mock_repo_class.return_value
        rule = AlertRule(id="tg_12345", pincode=None, lat=12.0, lng=77.0)
        repo_mock.get_rule.return_value = rule
        
        await process_telegram_update(update, client_mock, token)
        repo_mock.save_rule.assert_called_once()
        saved_rule = repo_mock.save_rule.call_args[0][0]
        assert saved_rule.pincode == "800014"
        assert saved_rule.lat is not None
        assert saved_rule.lng is not None
        send_mock.assert_called_once()
        assert "Location updated successfully" in send_mock.call_args[0][3]

@pytest.mark.asyncio
async def test_telegram_bot_location_invalid():
    client_mock = AsyncMock()
    token = "test"
    update = {
        "message": {
            "chat": {"id": 12345},
            "text": "/location 12.0,77.0",
            "date": 123456789
        }
    }
    with patch("app.notifications.telegram_bot.Database"), \
         patch("app.notifications.telegram_bot.AlertRepository") as mock_repo_class, \
         patch("app.notifications.telegram_bot._send_message", new_callable=AsyncMock) as send_mock:
        repo_mock = mock_repo_class.return_value
        rule = AlertRule(id="tg_12345", pincode=None, lat=12.0, lng=77.0)
        repo_mock.get_rule.return_value = rule
        
        await process_telegram_update(update, client_mock, token)
        repo_mock.save_rule.assert_not_called()
        send_mock.assert_called_once()
        assert "Invalid pincode" in send_mock.call_args[0][3]

@pytest.mark.asyncio
async def test_telegram_bot_status_empty():
    client_mock = AsyncMock()
    token = "test"
    update = {
        "message": {
            "chat": {"id": 12345},
            "text": "/status",
            "date": 123456789
        }
    }
    with patch("app.notifications.telegram_bot.Database"), \
         patch("app.notifications.telegram_bot.AlertRepository") as mock_repo_class, \
         patch("app.notifications.telegram_bot._send_message", new_callable=AsyncMock) as send_mock:
        repo_mock = mock_repo_class.return_value
        rule = AlertRule(id="tg_12345", enabled=True, keywords=[])
        repo_mock.get_rule.return_value = rule
        
        await process_telegram_update(update, client_mock, token)
        send_mock.assert_called_once()
        assert "Tracking: Not running" in send_mock.call_args[0][3]
        assert "Reason: No tracking targets configured" in send_mock.call_args[0][3]

@pytest.mark.asyncio
async def test_telegram_bot_status_active():
    client_mock = AsyncMock()
    token = "test"
    update = {
        "message": {
            "chat": {"id": 12345},
            "text": "/status",
            "date": 123456789
        }
    }
    with patch("app.notifications.telegram_bot.Database"), \
         patch("app.notifications.telegram_bot.AlertRepository") as mock_repo_class, \
         patch("app.notifications.telegram_bot._send_message", new_callable=AsyncMock) as send_mock:
        repo_mock = mock_repo_class.return_value
        rule = AlertRule(id="tg_12345", enabled=True, keywords=["test"])
        repo_mock.get_rule.return_value = rule
        
        await process_telegram_update(update, client_mock, token)
        send_mock.assert_called_once()
        assert "Tracking: Active" in send_mock.call_args[0][3]

@pytest.mark.asyncio
async def test_telegram_bot_resume_empty():
    client_mock = AsyncMock()
    token = "test"
    update = {
        "message": {
            "chat": {"id": 12345},
            "text": "/resume",
            "date": 123456789
        }
    }
    with patch("app.notifications.telegram_bot.Database"), \
         patch("app.notifications.telegram_bot.AlertRepository") as mock_repo_class, \
         patch("app.notifications.telegram_bot._send_message", new_callable=AsyncMock) as send_mock:
        repo_mock = mock_repo_class.return_value
        rule = AlertRule(id="tg_12345", enabled=False, keywords=[])
        repo_mock.get_rule.return_value = rule
        
        await process_telegram_update(update, client_mock, token)
        repo_mock.save_rule.assert_not_called()
        send_mock.assert_called_once()
        assert "Tracking cannot start yet" in send_mock.call_args[0][3]

@pytest.mark.asyncio
async def test_telegram_bot_resume_active():
    client_mock = AsyncMock()
    token = "test"
    update = {
        "message": {
            "chat": {"id": 12345},
            "text": "/resume",
            "date": 123456789
        }
    }
    with patch("app.notifications.telegram_bot.Database"), \
         patch("app.notifications.telegram_bot.AlertRepository") as mock_repo_class, \
         patch("app.notifications.telegram_bot._send_message", new_callable=AsyncMock) as send_mock:
        repo_mock = mock_repo_class.return_value
        rule = AlertRule(id="tg_12345", enabled=False, keywords=["test"])
        repo_mock.get_rule.return_value = rule
        
        await process_telegram_update(update, client_mock, token)
        repo_mock.save_rule.assert_called_once()
        assert repo_mock.save_rule.call_args[0][0].enabled is True
        send_mock.assert_called_once()
        assert "Tracking resumed" in send_mock.call_args[0][3]
