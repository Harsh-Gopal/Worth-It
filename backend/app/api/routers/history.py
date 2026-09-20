from typing import List
from fastapi import APIRouter, Depends

from app.api.schemas import PriceObservationResponse
from app.persistence.database import Database
from app.api.routers.search import get_db

router = APIRouter()

@router.get("/recent", response_model=List[dict])
async def get_recent_history(
    limit: int = 50,
    db: Database = Depends(get_db)
):
    with db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM alert_events 
            ORDER BY triggered_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
        
    return [dict(row) for row in rows]

@router.get("/{instamart_product_id}", response_model=List[PriceObservationResponse])
async def get_product_history(
    instamart_product_id: str,
    db: Database = Depends(get_db)
):
    with db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM price_observations 
            WHERE instamart_product_id = ?
            ORDER BY timestamp DESC
            """,
            (instamart_product_id,)
        ).fetchall()
        
    return [dict(row) for row in rows]
