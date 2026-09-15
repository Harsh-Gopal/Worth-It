import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    center_lat: float = 12.9716
    center_lng: float = 77.5946
    local_store_id: str = "store_local_123"
    
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    
    @property
    def database_path(self) -> Path:
        self.data_dir.mkdir(exist_ok=True)
        return self.data_dir / "alerts.db"
        
    @property
    def store_cache_path(self) -> Path:
        self.data_dir.mkdir(exist_ok=True)
        return self.data_dir / "stores.db"

def get_settings() -> Settings:
    return Settings()
