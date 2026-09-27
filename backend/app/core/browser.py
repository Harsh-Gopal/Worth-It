import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Playwright, Browser, Page, BrowserContext

log = logging.getLogger("browser_manager")

class BrowserManager:
    """
    Centralized Playwright resource manager.
    Prevents launching multiple Chromium instances and bounds concurrency
    to keep RAM usage low for free-tier deployments.
    """
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _lock = asyncio.Lock()
    _semaphore = asyncio.Semaphore(3)  # Maximum 3 concurrent page operations

    @classmethod
    async def ensure_started(cls):
        async with cls._lock:
            if cls._browser is None:
                log.info("Starting global Playwright browser instance...")
                try:
                    cls._playwright = await async_playwright().start()
                    cls._browser = await cls._playwright.firefox.launch(
                        headless=True,
                    )
                    log.info("Global Playwright browser (Firefox) started successfully.")
                except Exception as e:
                    log.error(f"Failed to start global Playwright instance: {e}", exc_info=True)
                    if cls._playwright:
                        await cls._playwright.stop()
                        cls._playwright = None
                    raise e

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls._browser:
                log.info("Closing global Playwright browser...")
                await cls._browser.close()
                cls._browser = None
            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None
                log.info("Playwright stopped.")

    @classmethod
    @asynccontextmanager
    async def get_page(cls, context_options: dict = None) -> AsyncGenerator[Page, None]:
        """
        Context manager to acquire a managed Playwright page with concurrency bounds.
        Use this instead of launching new browsers.
        """
        await cls.ensure_started()
        
        async with cls._semaphore:
            context = None
            page = None
            try:
                opts = context_options or {}
                if cls._browser is None:
                    raise RuntimeError("Browser is not initialized.")
                context = await cls._browser.new_context(**opts)
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
