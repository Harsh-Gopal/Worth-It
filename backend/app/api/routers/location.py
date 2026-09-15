import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.platforms.instamart.client import geocode, select_store

router = APIRouter()

class LocationResolveRequest(BaseModel):
    query: str

class LocationResponse(BaseModel):
    lat: float
    lng: float
    address: str
    title: str
    matched: str
    local_store_id: Optional[str] = None

def get_http_client():
    client = httpx.Client(timeout=15.0)
    try:
        yield client
    finally:
        client.close()

@router.get("/resolve", response_model=LocationResponse)
def resolve_location_get(
    address: str = Query(..., description="Pincode or address to resolve"),
    client: httpx.Client = Depends(get_http_client)
):
    """Resolve a pincode/address to coordinates and Instamart store ID (GET)."""
    try:
        place = geocode(client, address)
        store_id = select_store(client, place)
        return LocationResponse(
            lat=place["lat"],
            lng=place["lng"],
            address=place["address"],
            title=place["title"],
            matched=place["matched"],
            local_store_id=store_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/resolve", response_model=LocationResponse)
def resolve_location(
    req: LocationResolveRequest,
    client: httpx.Client = Depends(get_http_client)
):
    """Resolve a pincode/address to coordinates and Instamart store ID (POST)."""
    try:
        place = geocode(client, req.query)
        store_id = select_store(client, place)
        return LocationResponse(
            lat=place["lat"],
            lng=place["lng"],
            address=place["address"],
            title=place["title"],
            matched=place["matched"],
            local_store_id=store_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
