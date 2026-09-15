import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent

load_dotenv(ROOT / ".env")

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
BUILD_VERSION = "2.367.0"
API = "https://www.swiggy.com/api/instamart"

@dataclass
class Settings:
    data_dir: Path
    proxy: str | None = None
    headless: bool = True
    block_images: bool = True
    bootstrap_seconds: int = 30
    browser_profile: bool = False

settings = Settings(
    data_dir=Path(os.getenv("IM_DATA_DIR") or ROOT / "data"),
    proxy=os.getenv("PROXY_URL"),
    headless=os.getenv("IM_HEADLESS", "1") != "0",
    block_images=os.getenv("IM_BLOCK_IMAGES", "1") != "0",
    bootstrap_seconds=int(os.getenv("IM_BOOTSTRAP_SECONDS", "30")),
)

settings.data_dir.mkdir(parents=True, exist_ok=True)
