import os
import json
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel
from app.config import get_settings

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
    setup_required: bool
    is_unlocked: bool

def is_production() -> bool:
    # Determine if running in production (Render injects RENDER)
    return os.environ.get("RENDER") is not None or os.environ.get("VERCEL") is not None

def get_admin_pin() -> str | None:
    # 1. Environment variable (always takes precedence, mandatory in prod)
    env_pin = os.environ.get("WORTH_IT_ADMIN_PIN")
    if env_pin:
        return env_pin
        
    # 2. Local settings file (only for localhost development)
    if not is_production():
        settings = get_settings()
        settings_file = settings.data_dir / "user_settings.json"
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                # Return the locally configured PIN if it exists, otherwise "disabled" if they opted out
                return data.get("local_admin_pin")
            except Exception:
                pass
    return None

def verify_auth(request: Request):
    """
    FastAPI dependency to protect mutation endpoints.
    """
    pin = get_admin_pin()
    
    # If local dev and they explicitly opted out (pin == "disabled"), allow.
    if not is_production() and pin == "disabled":
        return True
        
    # If production and no PIN is set, fail securely.
    if is_production() and not pin:
        raise HTTPException(
            status_code=500, 
            detail="Production environment requires WORTH_IT_ADMIN_PIN environment variable."
        )
        
    # If local dev and no PIN set yet, they need to run setup.
    if not pin:
        raise HTTPException(
            status_code=401,
            detail="Security setup required. Please configure a PIN."
        )

    # Check session cookie
    token = request.cookies.get("worthit_session")
    if not token or token not in _sessions:
        raise HTTPException(status_code=401, detail="Unauthorized. Please unlock the application.")
        
    expiry = _sessions[token]
    if datetime.utcnow() > expiry:
        del _sessions[token]
        raise HTTPException(status_code=401, detail="Session expired. Please unlock again.")
        
    # Extend session
    _sessions[token] = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRY_MINUTES)
    return True


@router.get("/status", response_model=AuthStatus)
def get_status(request: Request):
    pin = get_admin_pin()
    is_prod = is_production()
    
    setup_required = False
    if not is_prod and not pin:
        setup_required = True
        
    is_unlocked = False
    if not is_prod and pin == "disabled":
        is_unlocked = True
    else:
        token = request.cookies.get("worthit_session")
        if token and token in _sessions and datetime.utcnow() <= _sessions[token]:
            is_unlocked = True
            
    return AuthStatus(
        is_production=is_prod,
        setup_required=setup_required,
        is_unlocked=is_unlocked
    )

@router.post("/setup")
def setup_security(req: SetupRequest):
    if is_production():
        raise HTTPException(status_code=403, detail="Setup must be done via environment variables in production.")
        
    if get_admin_pin():
        raise HTTPException(status_code=400, detail="Security is already configured.")
        
    if req.pin != "disabled":
        if not req.pin or len(req.pin) < 4:
            raise HTTPException(status_code=400, detail="PIN must be at least 4 characters.")
        if req.pin != req.confirm_pin:
            raise HTTPException(status_code=400, detail="PINs do not match.")
            
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings.data_dir / "user_settings.json"
    
    data = {}
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text())
        except:
            pass
            
    data["local_admin_pin"] = req.pin
    settings_file.write_text(json.dumps(data, indent=2))
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
    _sessions[token] = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRY_MINUTES)
    
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
