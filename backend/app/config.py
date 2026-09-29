import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    center_lat: float = 12.9716
    center_lng: float = 77.5946
    local_store_id: str | None = None
    
    playwright_enabled: bool = False
    max_external_requests_per_scan: int = 100
    max_concurrent_requests: int = 3
    max_locations_per_scan: int = 20
    serviceability_cache_ttl: int = 600
    store_discovery_cache_ttl: int = 600
    request_timeout: float = 15.0
    max_retries: int = 1
    
    data_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
    )
    
    @property
    def database_path(self) -> Path:
        self.data_dir.mkdir(exist_ok=True)
        return self.data_dir / "alerts.db"
        
    @property
    def store_cache_path(self) -> Path:
        self.data_dir.mkdir(exist_ok=True)
        return self.data_dir / "stores.db"

    app_version: str = "Version Unknown"

_cached_version = None

def get_settings() -> Settings:
    global _cached_version
    settings = Settings()
    
    if _cached_version is not None:
        settings.app_version = _cached_version
        return settings
        
    if os.getenv("APP_VERSION"):
        _cached_version = os.getenv("APP_VERSION")
        settings.app_version = _cached_version
        return settings
        
    if os.getenv("GIT_COMMIT_SHA"):
        _cached_version = f"Version • {os.getenv('GIT_COMMIT_SHA')[:7]}"
        settings.app_version = _cached_version
        return settings
        
    if os.getenv("VERCEL_GIT_COMMIT_SHA"):
        _cached_version = f"Version • {os.getenv('VERCEL_GIT_COMMIT_SHA')[:7]}"
        settings.app_version = _cached_version
        return settings
        
    version_file = Path(__file__).resolve().parent.parent / "VERSION.txt"
    if version_file.exists():
        try:
            count = version_file.read_text().strip()
            if count and count != "Unknown":
                _cached_version = f"Version 0.{count}"
                settings.app_version = _cached_version
                return settings
        except Exception:
            pass

    try:
        import subprocess
        commit_count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'], 
            stderr=subprocess.DEVNULL,
            cwd=str(Path(__file__).parent)
        ).decode('utf-8').strip()
        _cached_version = f"Version 0.{commit_count}"
        settings.app_version = _cached_version
    except Exception:
        _cached_version = settings.app_version
        
    return settings
