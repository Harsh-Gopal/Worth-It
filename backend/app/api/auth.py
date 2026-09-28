import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel
from app.config import get_settings
from app.persistence.database import Database
from app.persistence.repositories.settings_repo import SettingsRepository

router = APIRouter()

# In-memory session store (dictionary of token -> expiry)
# Since the app runs in a single process usually, this is fine for lightweight auth.
_sessions = {}
SESSION_EXPIRY_MINUTES = 60

class SetupRequest(BaseModel):
    pin: str
    confirm_pin: str

class UnlockRequest(BaseModel):
    pin: str

class AuthStatus(BaseModel):
    is_production: bool
    security_enabled: bool
    is_unlocked: bool

def is_production() -> bool:
    return os.environ.get("RENDER") is not None or os.environ.get("VERCEL") is not None

def is_security_enabled() -> bool:
    if os.environ.get("WORTH_IT_ADMIN_PIN"):
        return True
    if not is_production():
        try:
            db = Database(get_settings().database_path)
            repo = SettingsRepository(db)
            data = repo.get_user_settings()
            pin = data.get("local_admin_pin")
            if pin and pin != "disabled":
                return True
        except:
            pass
    return False

def get_admin_pin() -> str | None:
    env_pin = os.environ.get("WORTH_IT_ADMIN_PIN")
    if env_pin:
        return env_pin
        
    if not is_production():
        try:
            db = Database(get_settings().database_path)
            repo = SettingsRepository(db)
            data = repo.get_user_settings()
            return data.get("local_admin_pin")
        except:
            pass
    return None

def verify_auth(request: Request):
    """
    FastAPI dependency to protect mutation endpoints.
    """
    if not is_security_enabled():
        return True
        
    # Check session cookie
    token = request.cookies.get("worthit_session")
    if not token or token not in _sessions:
        raise HTTPException(status_code=401, detail="Unauthorized. Please unlock the application.")
        
    expiry = _sessions[token]
    if datetime.now(timezone.utc) > expiry:
        del _sessions[token]
        raise HTTPException(status_code=401, detail="Session expired. Please unlock again.")
        
    # Extend session
    _sessions[token] = datetime.now(timezone.utc) + timedelta(minutes=SESSION_EXPIRY_MINUTES)
    return True


@router.get("/status", response_model=AuthStatus)
def get_status(request: Request):
    is_prod = is_production()
    security_enabled = is_security_enabled()
    
    is_unlocked = False
    if not security_enabled:
        is_unlocked = True
    else:
        token = request.cookies.get("worthit_session")
        if token and token in _sessions and datetime.now(timezone.utc) <= _sessions[token]:
            is_unlocked = True
            
    return AuthStatus(
        is_production=is_prod,
        security_enabled=security_enabled,
        is_unlocked=is_unlocked
    )

@router.post("/setup")
def setup_security(req: SetupRequest):
    if is_production():
        raise HTTPException(status_code=403, detail="Setup must be done via environment variables in production.")
        
    if req.pin != "disabled":
        if not req.pin or len(req.pin) < 4:
            raise HTTPException(status_code=400, detail="PIN must be at least 4 characters.")
        if req.pin != req.confirm_pin:
            raise HTTPException(status_code=400, detail="PINs do not match.")
            
    try:
        db = Database(get_settings().database_path)
        repo = SettingsRepository(db)
        data = repo.get_user_settings()
        data["local_admin_pin"] = req.pin
        repo.save_user_settings(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True}

@router.post("/unlock")
def unlock(req: UnlockRequest, response: Response):
    correct_pin = get_admin_pin()
    
    if is_production() and not correct_pin:
        raise HTTPException(status_code=500, detail="WORTH_IT_ADMIN_PIN is not configured.")
        
    if not correct_pin or correct_pin == "disabled":
        return {"success": True}
        
    if req.pin != correct_pin:
        # TODO: Rate limiting
        raise HTTPException(status_code=401, detail="Incorrect PIN")
        
    token = secrets.token_urlsafe(32)
    _sessions[token] = datetime.now(timezone.utc) + timedelta(minutes=SESSION_EXPIRY_MINUTES)
    
    response.set_cookie(
        key="worthit_session",
        value=token,
        max_age=SESSION_EXPIRY_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=is_production()
    )
    return {"success": True}

@router.post("/lock")
def lock(request: Request, response: Response):
    token = request.cookies.get("worthit_session")
    if token in _sessions:
        del _sessions[token]
    response.delete_cookie("worthit_session")
    return {"success": True}
