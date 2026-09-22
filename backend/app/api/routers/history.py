from typing import List
from fastapi import APIRouter, Depends

from app.api.schemas import PriceObservationResponse
from app.persistence.database import Database
from app.api.routers.search import get_db
from app.domain.services.grouping_service import ProductGroupingService
from app.persistence.repositories.alert_repo import AlertRepository

router = APIRouter()

@router.get("/recent", response_model=List[dict])
async def get_recent_history(
    limit: int = 150, # Fetch more raw events so we can group them effectively
    tz_offset_mins: int = -330, # Default to IST
    db: Database = Depends(get_db)
):
    repo = AlertRepository(db)
    
    # 1. Clean up expired history before returning results
    repo.cleanup_expired_history(days=7)
    
    events = repo.get_all_events(limit=limit)
    
    grouped = ProductGroupingService.group_events(events, tz_offset_mins=tz_offset_mins)
    # Convert models to dicts for JSON serialization
    return [g.model_dump() for g in grouped][:50] # Return top 50 groups

@router.get("/{instamart_product_id}", response_model=List[PriceObservationResponse])
async def get_product_history(
    instamart_product_id: str,
    db: Database = Depends(get_db)
):
    with db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT price, triggered_at as timestamp 
            FROM alert_events 
            WHERE instamart_product_id = ?
            ORDER BY triggered_at ASC
            """,
            (instamart_product_id,)
        ).fetchall()
        
    return [{"price": row["price"], "timestamp": row["timestamp"]} for row in rows]

@router.delete("/date/{date_str}")
async def delete_history_for_date(
    date_str: str,
    tz_offset_mins: int = -330, # Default IST
    db: Database = Depends(get_db)
):
    """
    Delete all history events for a specific local date (YYYY-MM-DD).
    """
    # Basic validation of YYYY-MM-DD
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD")
        
    repo = AlertRepository(db)
    
    from datetime import datetime, timezone, timedelta
    
    now_utc = datetime.now(timezone.utc)
    # Calculate today's local date string
    now_local = now_utc - timedelta(minutes=tz_offset_mins)
    today_local_str = now_local.strftime("%Y-%m-%d")
    
    if date_str == today_local_str:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Cannot delete today's history")
    
    try:
        # local_start = YYYY-MM-DD 00:00:00
        # For timezone offset in JS, e.g. IST is -330 minutes
        # UTC + offset = Local. So UTC = Local - offset
        # Let's create naive datetime for the date at midnight
        local_start = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Calculate the UTC start and end bounds
        utc_start = (local_start + timedelta(minutes=tz_offset_mins)).replace(tzinfo=timezone.utc)
        utc_end = utc_start + timedelta(days=1)
        
        utc_start_str = utc_start.isoformat()
        utc_end_str = utc_end.isoformat()
        
        deleted_count = repo.delete_history_by_utc_bounds(utc_start_str, utc_end_str)
        return {"message": "History deleted", "deleted_count": deleted_count, "date": date_str}
    except Exception as e:
        import logging
        logging.error(f"Error calculating UTC bounds for date deletion: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to delete date history")
