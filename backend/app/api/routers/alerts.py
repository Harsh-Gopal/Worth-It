"""
Alerts router — CRUD for persistent deal alert rules.
"""
import uuid
import httpx
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from app.domain.services.broadcast import broadcaster

from app.api.schemas import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertEventResponse
from app.domain.models.alert import AlertRule
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.domain.services.alert_runner import AlertRunner
from app.notifications.telegram import TelegramNotificationProvider
from app.notifications.provider import NotificationService
from app.config import get_settings
from app.api.routers.search import get_db, get_store_cache, get_price_history
from app.platforms.swiggy import SwiggyClient

router = APIRouter()


def get_alert_repo(db: Database = Depends(get_db)) -> AlertRepository:
    return AlertRepository(db)


async def get_notification_service():
    async with httpx.AsyncClient(timeout=15.0) as async_client:
        telegram = TelegramNotificationProvider(async_client)
        yield NotificationService([telegram])


# ─── SINGLE INSTANCE MONITOR ──────────────────────────────────────────────────────

@router.post("/primary", response_model=AlertRuleResponse)
async def upsert_primary_alert(
    rule_in: AlertRuleCreate,
    repo: AlertRepository = Depends(get_alert_repo),
):
    if not rule_in.lat or not rule_in.lng:
        raise HTTPException(status_code=400, detail="Location (lat/lng) is required.")
        
    has_target = bool(rule_in.keywords or rule_in.categories or rule_in.product_urls)
    if not has_target:
        raise HTTPException(status_code=400, detail="At least one keyword, category, or product URL is required.")

    now = datetime.now(timezone.utc)
    rule = AlertRule(
        id="primary_monitor",
        name="Primary Monitor",
        categories=rule_in.categories,
        category_rules=rule_in.category_rules,
        keywords=rule_in.keywords,
        keyword_rules=rule_in.keyword_rules,
        exclude_keywords=rule_in.exclude_keywords,
        product_urls=rule_in.product_urls,
        min_discount_pct=None,
        max_price=rule_in.max_price,
        min_price_drop_pct=rule_in.min_price_drop_pct,
        require_historical_low=rule_in.require_historical_low,
        condition_operator=rule_in.condition_operator,
        require_in_stock=rule_in.require_in_stock,
        radius_km=min(rule_in.radius_km, 20.0),
        expansion_strategy=rule_in.expansion_strategy,
        ranking_strategy=rule_in.ranking_strategy,
        cooldown_hours=rule_in.cooldown_hours,
        lat=rule_in.lat,
        lng=rule_in.lng,
        pincode=rule_in.pincode,
        local_store_id=rule_in.local_store_id,
        platforms=rule_in.platforms,
        telegram_recipient_ids=rule_in.telegram_recipient_ids,
        run_interval_minutes=rule_in.run_interval_minutes,
        created_at=now,
        updated_at=now,
        enabled=True
    )
    saved = repo.save_rule(rule)
    return saved


@router.get("/primary", response_model=AlertRuleResponse)
async def get_primary_alert(repo: AlertRepository = Depends(get_alert_repo)):
    rule = repo.get_rule("primary_monitor")
    if not rule:
        raise HTTPException(status_code=404, detail="Primary monitor not found")
    return rule


@router.patch("/primary/stop", response_model=AlertRuleResponse)
async def stop_primary_alert(repo: AlertRepository = Depends(get_alert_repo)):
    rule = repo.get_rule("primary_monitor")
    if not rule:
        raise HTTPException(status_code=404, detail="Primary monitor not found")
    rule.enabled = False
    rule.updated_at = datetime.now(timezone.utc)
    saved = repo.save_rule(rule)
    await broadcaster.publish("alert_primary_monitor", {"event": "watch_deleted", "data": {}})
    
    from app.domain.services.alert_runner import _active_runs
    if "primary_monitor" in _active_runs:
        _active_runs["primary_monitor"].set()
        
    return saved

# ─── CRUD ─────────────────────────────────────────────────────────────────────

@router.post("/", response_model=AlertRuleResponse)
async def create_alert(
    rule_in: AlertRuleCreate,
    repo: AlertRepository = Depends(get_alert_repo),
):
    now = datetime.now(timezone.utc)
    rule = AlertRule(
        id=str(uuid.uuid4()),
        name=rule_in.name or f"Alert {now.strftime('%Y-%m-%d %H:%M')}",
        categories=rule_in.categories,
        category_rules=rule_in.category_rules,
        keywords=rule_in.keywords,
        keyword_rules=rule_in.keyword_rules,
        exclude_keywords=rule_in.exclude_keywords,
        product_urls=rule_in.product_urls,
        min_discount_pct=None,
        max_price=rule_in.max_price,
        min_price_drop_pct=rule_in.min_price_drop_pct,
        require_historical_low=rule_in.require_historical_low,
        condition_operator=rule_in.condition_operator,
        require_in_stock=rule_in.require_in_stock,
        radius_km=min(rule_in.radius_km, 20.0),
        expansion_strategy=rule_in.expansion_strategy,
        ranking_strategy=rule_in.ranking_strategy,
        cooldown_hours=rule_in.cooldown_hours,
        lat=rule_in.lat,
        lng=rule_in.lng,
        local_store_id=rule_in.local_store_id,
        platforms=rule_in.platforms,
        telegram_recipient_ids=rule_in.telegram_recipient_ids,
        run_interval_minutes=rule_in.run_interval_minutes,
        created_at=now,
        updated_at=now,
    )
    saved = repo.save_rule(rule)
    return saved


@router.get("/", response_model=List[AlertRuleResponse])
async def list_alerts(repo: AlertRepository = Depends(get_alert_repo)):
    return repo.get_all_rules()


@router.get("/events", response_model=List[AlertEventResponse])
async def get_all_alert_events(
    limit: int = 100,
    repo: AlertRepository = Depends(get_alert_repo),
):
    """Get global history of all triggered alerts across all rules."""
    return repo.get_all_events(limit=limit)


@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_alert(rule_id: str, repo: AlertRepository = Depends(get_alert_repo)):
    rule = repo.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert not found")
    return rule


@router.patch("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert(
    rule_id: str,
    update_in: AlertRuleUpdate,
    repo: AlertRepository = Depends(get_alert_repo),
):
    rule = repo.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert not found")

    if update_in.enabled is not None:
        rule.enabled = update_in.enabled
    if update_in.name is not None:
        rule.name = update_in.name
    if update_in.cooldown_hours is not None:
        rule.cooldown_hours = update_in.cooldown_hours
    if update_in.telegram_recipient_ids is not None:
        rule.telegram_recipient_ids = update_in.telegram_recipient_ids

    rule.updated_at = datetime.now(timezone.utc)
    return repo.save_rule(rule)


@router.delete("/{rule_id}")
async def delete_alert(rule_id: str, repo: AlertRepository = Depends(get_alert_repo)):
    rule = repo.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    from app.domain.services.alert_runner import _active_runs
    if rule_id in _active_runs:
        _active_runs[rule_id].set()
        
    repo.delete_rule(rule_id)
    await broadcaster.publish(f"alert_{rule_id}", {"event": "watch_deleted", "data": {}})
    return {"status": "deleted", "id": rule_id}


@router.get("/{rule_id}/events", response_model=List[AlertEventResponse])
async def get_alert_events(
    rule_id: str,
    repo: AlertRepository = Depends(get_alert_repo),
):
    return repo.get_events_for_rule(rule_id)


def _trigger_alert_run(rule_id: str, repo: AlertRepository, store_cache, price_history):
    rule = repo.get_rule(rule_id)
    if not rule:
        return False
        
    now = datetime.now(timezone.utc)
    rule.last_run_at = now
    repo.save_rule(rule)

    settings = get_settings()

    async def run_background():
        try:
            async with httpx.AsyncClient(timeout=15.0) as async_client:
                telegram = TelegramNotificationProvider(async_client)
                ns = NotificationService([telegram])

                from app.platforms.factory import get_platform_client
                active_clients = []
                for plat in rule.platforms:
                    try:
                        active_clients.append(get_platform_client(plat))
                    except Exception as e:
                        import logging
                        logging.getLogger("alert_runner").warning(f"Could not load client for platform {plat}: {e}")

                runner = AlertRunner(
                    alert_repo=repo,
                    store_cache=store_cache,
                    price_history=price_history,
                    notification_service=ns,
                    clients=active_clients,
                    center_lat=rule.lat if rule.lat is not None else settings.center_lat,
                    center_lng=rule.lng if rule.lng is not None else settings.center_lng,
                    local_store_id=rule.local_store_id if rule.local_store_id else settings.local_store_id,
                )
                await runner.run_rule(rule)
        except Exception as e:
            import logging
            logging.getLogger("alert_runner").error("Background run failed", exc_info=True)
            await broadcaster.publish(f"alert_{rule.id}", {"event": "search_error", "data": {"message": str(e)}})

    asyncio.create_task(run_background())
    return True

@router.post("/{rule_id}/run", response_model=dict)
async def run_alert_now(
    rule_id: str,
    repo: AlertRepository = Depends(get_alert_repo),
    store_cache=Depends(get_store_cache),
    price_history=Depends(get_price_history),
):
    if not _trigger_alert_run(rule_id, repo, store_cache, price_history):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "started", "rule_id": rule_id}

@router.get("/{rule_id}/stream")
async def stream_alert_events(
    rule_id: str,
    trigger_run: bool = False,
    repo: AlertRepository = Depends(get_alert_repo),
    store_cache=Depends(get_store_cache),
    price_history=Depends(get_price_history),
):
    """Subscribe to live scan events for a specific alert."""
    topic = f"alert_{rule_id}"
    
    async def event_generator():
        queue = await broadcaster.subscribe(topic)
        
        if trigger_run:
            _trigger_alert_run(rule_id, repo, store_cache, price_history)
            
        try:
            while True:
                event_dict = await queue.get()
                if "event" in event_dict and "data" in event_dict:
                    yield {
                        "event": event_dict["event"],
                        "data": json.dumps(event_dict["data"])
                    }
                if event_dict["event"] == "watch_deleted":
                    break
        except asyncio.CancelledError:
            pass
        finally:
            broadcaster.unsubscribe(topic, queue)
            
    return EventSourceResponse(event_generator())
