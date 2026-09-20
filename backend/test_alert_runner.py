import asyncio
from app.persistence.database import Database
from app.persistence.repositories.alert_repo import AlertRepository
from app.persistence.repositories.price_history_repo import PriceHistoryRepository
from app.geo.store_cache import StoreCache
from app.domain.services.price_history_service import PriceHistoryService
from app.notifications.provider import NotificationService
from app.platforms.swiggy import SwiggyClient
from app.domain.services.alert_runner import AlertRunner

async def main():
    db = Database("data/alerts.db")
    repo = AlertRepository(db)
    store_cache = StoreCache("data/stores.db")
    price_history = PriceHistoryService(PriceHistoryRepository(db))
    
    ns = NotificationService([])
    swiggy = SwiggyClient()
    
    rule = repo.get_rule("primary_monitor")
    if not rule:
        print("Rule not found")
        return
        
    print(f"Running rule {rule.id}, keywords={rule.keywords}, lat={rule.lat}, lng={rule.lng}")
    
    runner = AlertRunner(
        alert_repo=repo,
        store_cache=store_cache,
        price_history=price_history,
        notification_service=ns,
        client=swiggy,
        center_lat=rule.lat,
        center_lng=rule.lng,
        local_store_id=rule.local_store_id
    )
    
    from app.domain.services.broadcast import broadcaster
    
    async def listen():
        q = await broadcaster.subscribe(f"alert_{rule.id}")
        while True:
            ev = await q.get()
            print("BROADCAST:", ev)
            if ev["event"] == "search_completed":
                break
                
    t = asyncio.create_task(listen())
    
    new_events = await runner.run_rule(rule)
    print("NEW EVENTS RETURNED:", len(new_events))
    await t

if __name__ == "__main__":
    asyncio.run(main())
