import os
from pathlib import Path
from pydantic_settings import BaseSettings

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
    
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    
    @property
    def database_path(self) -> Path:
        self.data_dir.mkdir(exist_ok=True)
        return self.data_dir / "alerts.db"
        
    @property
    def store_cache_path(self) -> Path:
        self.data_dir.mkdir(exist_ok=True)
        return self.data_dir / "stores.db"

    app_version: str = "Version Unknown"

def get_settings() -> Settings:
    settings = Settings()
    try:
        import subprocess
        commit_count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'], 
            stderr=subprocess.DEVNULL,
            cwd=str(Path(__file__).parent)
        ).decode('utf-8').strip()
        settings.app_version = f"Version 0.{commit_count}"
    except Exception:
        pass
    return settings
