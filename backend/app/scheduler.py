"""
Background alert scheduler.

Runs all enabled AlertRules on a configurable interval (default: every 30 minutes).
Uses APScheduler with AsyncIO backend so it integrates cleanly with FastAPI's event loop.

Per-alert `run_interval_minutes` overrides the global interval:
  - 0 = use the global default
  - N = run every N minutes (minimum 5 to prevent abuse)
"""
import logging
import os
import fcntl
import psutil
from typing import Optional

import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger("scheduler")

GLOBAL_INTERVAL_MINUTES = 1  # Tick every minute, check rules individually
MIN_INTERVAL_MINUTES = 5

_scheduler: Optional[AsyncIOScheduler] = None
_lock_file = None


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
    from app.platforms.swiggy import SwiggyClient

    settings = get_settings()

    db = Database(settings.database_path)
    repo = AlertRepository(db)
    
    # Always clean up expired history (older than 7 days) on each scheduler tick
    try:
        deleted = repo.cleanup_expired_history(days=7)
        if deleted > 0:
            log.info("Scheduler: cleaned up %d expired history event(s)", deleted)
    except Exception as e:
        log.warning("Scheduler: history cleanup failed: %s", e)
    
    rules = repo.get_active_rules()

    if not rules:
        log.debug("No active alert rules to run")
        return

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    rules_to_run = []
    for rule in rules:
        interval = max(rule.run_interval_minutes or MIN_INTERVAL_MINUTES, MIN_INTERVAL_MINUTES)
        
        # If last_run_at is None, we run it immediately
        if rule.last_run_at is None:
            rules_to_run.append(rule)
            continue
            
        # Ensure last_run_at is timezone-aware for comparison
        last_run_at_tz = rule.last_run_at
        if last_run_at_tz.tzinfo is None:
            last_run_at_tz = last_run_at_tz.replace(tzinfo=timezone.utc)
            
        elapsed_minutes = (now - last_run_at_tz).total_seconds() / 60
        if elapsed_minutes >= interval:
            rules_to_run.append(rule)

    if not rules_to_run:
        log.debug("No rules due to run yet")
        return

    # Update last_run_at immediately to prevent duplicate scheduling
    for rule in rules_to_run:
        rule.last_run_at = now
        repo.save_rule(rule)

    log.info("Scheduler: running %d due alert rule(s)", len(rules_to_run))

    # Shared session for all rule runs in this batch
    async with httpx.AsyncClient(timeout=15.0) as async_client:
        with httpx.Client(timeout=20.0) as sync_client:
            from app.geo.store_cache import get_global_cache
            store_cache = get_global_cache(settings.store_cache_path)
            price_history = PriceHistoryService(
                PriceHistoryRepository(Database(settings.database_path))
            )
            notification_service = NotificationService(
                [TelegramNotificationProvider(async_client)]
            )

            for rule in rules_to_run:
                try:
                    runner = AlertRunner(
                        alert_repo=repo,
                        store_cache=store_cache,
                        price_history=price_history,
                        notification_service=notification_service,
                        client=SwiggyClient(),
                        center_lat=rule.lat if rule.lat is not None else settings.center_lat,
                        center_lng=rule.lng if rule.lng is not None else settings.center_lng,
                        local_store_id=rule.local_store_id or settings.local_store_id,
                    )
                    events = await runner.run_rule(rule)
                    log.info("Alert rule %s (%s) fired %d event(s)", rule.id, rule.name, len(events))
                except Exception as e:
                    log.error("Alert rule %s failed: %s", rule.id, e, exc_info=True)


def start_scheduler() -> Optional[AsyncIOScheduler]:
    global _scheduler, _lock_file
    if _scheduler and _scheduler.running:
        return _scheduler
        
    lock_path = "/tmp/worthit_scheduler.lock"
    
    # Check if lock exists and process is alive
    if os.path.exists(lock_path):
        try:
            with open(lock_path, "r") as f:
                pid = int(f.read().strip())
            if not psutil.pid_exists(pid):
                log.info(f"Removing stale lock file from dead PID {pid}")
                os.remove(lock_path)
        except Exception:
            pass

    try:
        _lock_file = open(lock_path, "w")
        fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
    except BlockingIOError:
        log.warning("Another scheduler instance is already running.")
        return None
    except Exception as e:
        log.error("Failed to acquire scheduler lock: %s", e)
        return None

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_all_active_alerts,
        trigger=IntervalTrigger(minutes=GLOBAL_INTERVAL_MINUTES),
        id="global_alert_runner",
        name="Global Alert Runner",
        replace_existing=True,
        misfire_grace_time=None,
        coalesce=True,
        max_instances=1,
    )
    _scheduler.start()
    log.info("Alert scheduler started (interval: %dm)", GLOBAL_INTERVAL_MINUTES)
    return _scheduler


def stop_scheduler():
    global _scheduler, _lock_file
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("Alert scheduler stopped")
        
    if _lock_file:
        try:
            fcntl.flock(_lock_file, fcntl.LOCK_UN)
            _lock_file.close()
            _lock_file = None
            os.remove("/tmp/worthit_scheduler.lock")
        except Exception:
            pass
