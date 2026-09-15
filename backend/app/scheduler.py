"""
Background alert scheduler.

Runs all enabled AlertRules on a configurable interval (default: every 30 minutes).
Uses APScheduler with AsyncIO backend so it integrates cleanly with FastAPI's event loop.

Per-alert `run_interval_minutes` overrides the global interval:
  - 0 = use the global default
  - N = run every N minutes (minimum 5 to prevent abuse)
"""
import logging
from typing import Optional

import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger("scheduler")

GLOBAL_INTERVAL_MINUTES = 30
MIN_INTERVAL_MINUTES = 5

_scheduler: Optional[AsyncIOScheduler] = None


async def _run_all_active_alerts():
    """Fetch all active rules and run each one."""
    from app.config import get_settings
    from app.persistence.database import Database
    from app.persistence.repositories.alert_repo import AlertRepository
    from app.persistence.repositories.price_history_repo import PriceHistoryRepository
    from app.domain.services.price_history_service import PriceHistoryService
    from app.domain.services.alert_runner import AlertRunner
    from app.notifications.telegram import TelegramNotificationProvider
    from app.notifications.provider import NotificationService
    from app.geo.store_cache import StoreCache

    settings = get_settings()

    db = Database(settings.database_path)
    repo = AlertRepository(db)
    rules = repo.get_active_rules()

    if not rules:
        log.debug("No active alert rules to run")
        return

    log.info("Scheduler: running %d active alert rule(s)", len(rules))

    # Shared session for all rule runs in this batch
    async with httpx.AsyncClient(timeout=15.0) as async_client:
        with httpx.Client(timeout=20.0) as sync_client:
            store_cache = StoreCache(settings.store_cache_path)
            price_history = PriceHistoryService(
                PriceHistoryRepository(Database(settings.database_path))
            )
            notification_service = NotificationService(
                [TelegramNotificationProvider(async_client)]
            )

            for rule in rules:
                try:
                    runner = AlertRunner(
                        alert_repo=repo,
                        store_cache=store_cache,
                        price_history=price_history,
                        notification_service=notification_service,
                        client=sync_client,
                        center_lat=rule.lat if rule.lat is not None else settings.center_lat,
                        center_lng=rule.lng if rule.lng is not None else settings.center_lng,
                        local_store_id=rule.local_store_id or settings.local_store_id,
                    )
                    events = await runner.run_rule(rule)
                    log.info("Alert rule %s (%s) fired %d event(s)", rule.id, rule.name, len(events))
                except Exception as e:
                    log.error("Alert rule %s failed: %s", rule.id, e, exc_info=True)


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_all_active_alerts,
        trigger=IntervalTrigger(minutes=GLOBAL_INTERVAL_MINUTES),
        id="global_alert_runner",
        name="Global Alert Runner",
        replace_existing=True,
    )
    _scheduler.start()
    log.info("Alert scheduler started (interval: %dm)", GLOBAL_INTERVAL_MINUTES)
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("Alert scheduler stopped")
