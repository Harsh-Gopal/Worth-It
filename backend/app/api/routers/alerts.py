"""
Alerts router — CRUD for persistent deal alert rules.
"""
import uuid
import httpx
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertEventResponse
from app.domain.models.alert import AlertRule
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.domain.services.alert_runner import AlertRunner
from app.notifications.telegram import TelegramNotificationProvider
from app.notifications.provider import NotificationService
from app.config import get_settings
from app.api.routers.search import get_db, get_store_cache, get_price_history, get_http_client

router = APIRouter()


def get_alert_repo(db: Database = Depends(get_db)) -> AlertRepository:
    return AlertRepository(db)


def get_notification_service() -> NotificationService:
    async_client = httpx.AsyncClient(timeout=15.0)
    telegram = TelegramNotificationProvider(async_client)
    return NotificationService([telegram])


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@router.post("/", response_model=AlertRuleResponse)
async def create_alert(
    rule_in: AlertRuleCreate,
    repo: AlertRepository = Depends(get_alert_repo),
):
    now = datetime.now(timezone.utc)
    rule = AlertRule(
        id=str(uuid.uuid4()),
        name=rule_in.name,
        categories=rule_in.categories,
        keywords=rule_in.keywords,
        exclude_keywords=rule_in.exclude_keywords,
        product_urls=rule_in.product_urls,
        min_discount_pct=rule_in.min_discount_pct,
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
    repo.delete_rule(rule_id)
    return {"status": "deleted", "id": rule_id}


@router.get("/{rule_id}/events", response_model=List[AlertEventResponse])
async def get_alert_events(
    rule_id: str,
    repo: AlertRepository = Depends(get_alert_repo),
):
    return repo.get_events_for_rule(rule_id)


@router.post("/{rule_id}/run", response_model=List[AlertEventResponse])
async def run_alert_now(
    rule_id: str,
    repo: AlertRepository = Depends(get_alert_repo),
    store_cache=Depends(get_store_cache),
    price_history=Depends(get_price_history),
    client: httpx.Client = Depends(get_http_client),
):
    rule = repo.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert not found")

    settings = get_settings()
    notification_service = get_notification_service()

    runner = AlertRunner(
        alert_repo=repo,
        store_cache=store_cache,
        price_history=price_history,
        notification_service=notification_service,
        client=client,
        center_lat=rule.lat if rule.lat is not None else settings.center_lat,
        center_lng=rule.lng if rule.lng is not None else settings.center_lng,
        local_store_id=rule.local_store_id if rule.local_store_id else settings.local_store_id,
    )

    new_events = await runner.run_rule(rule)
    return new_events
