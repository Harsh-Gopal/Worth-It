import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Playwright, Browser, Page, BrowserContext

log = logging.getLogger("browser_manager")

class BrowserManager:
    """
    Centralized Playwright resource manager.
    Prevents launching multiple Chromium/Firefox instances and bounds concurrency
    to keep RAM usage low for free-tier deployments.
    """
    _playwright: Optional[Playwright] = None
    _chromium: Optional[Browser] = None
    _firefox: Optional[Browser] = None
    _lock = asyncio.Lock()
    _semaphore = asyncio.Semaphore(3)  # Maximum 3 concurrent page operations

    @classmethod
    async def ensure_started(cls, browser_type: str = "chromium"):
        async with cls._lock:
            if cls._playwright is None:
                log.info("Starting global Playwright instance...")
                try:
                    cls._playwright = await asyncio.wait_for(async_playwright().start(), timeout=20.0)
                except Exception as e:
                    log.error(f"Failed to start Playwright: {e}", exc_info=True)
                    raise e

            if browser_type == "chromium" and cls._chromium is None:
                log.info("Starting global Chromium browser...")
                try:
                    cls._chromium = await asyncio.wait_for(
                        cls._playwright.chromium.launch(
                            headless=True,
                            args=["--disable-blink-features=AutomationControlled"]
                        ),
                        timeout=30.0
                    )
                except Exception as e:
                    log.error(f"Failed to start Chromium: {e}", exc_info=True)
                    raise e
                    
            if browser_type == "firefox" and cls._firefox is None:
                log.info("Starting global Firefox browser...")
                try:
                    cls._firefox = await asyncio.wait_for(
                        cls._playwright.firefox.launch(headless=True),
                        timeout=30.0
                    )
                except Exception as e:
                    log.error(f"Failed to start Firefox: {e}", exc_info=True)
                    raise e

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls._chromium:
                await cls._chromium.close()
                cls._chromium = None
            if cls._firefox:
                await cls._firefox.close()
                cls._firefox = None
            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None
                log.info("Playwright stopped.")

    @classmethod
    @asynccontextmanager
    async def get_page(cls, context_options: dict = None, browser_type: str = "chromium") -> AsyncGenerator[Page, None]:
        """
        Context manager to acquire a managed Playwright page with concurrency bounds.
        Use this instead of launching new browsers.
        browser_type can be "chromium" or "firefox".
        """
        await cls.ensure_started(browser_type)
        
        async with cls._semaphore:
            context = None
            page = None
            try:
                opts = context_options or {}
                browser = cls._chromium if browser_type == "chromium" else cls._firefox
                if browser is None:
                    raise RuntimeError(f"{browser_type.capitalize()} Browser is not initialized.")
                context = await browser.new_context(**opts)
                page = await context.new_page()
                yield page
            finally:
                if page:
                    try:
                        await page.close()
                    except Exception as e:
                        log.debug(f"Error closing page: {e}")
                if context:
                    try:
                        await context.close()
                    except Exception as e:
                        log.debug(f"Error closing context: {e}")
