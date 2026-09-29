import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Playwright, Browser, Page, BrowserContext, Error as PlaywrightError

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
            # Check if chromium is dead
            if cls._chromium and not cls._chromium.is_connected():
                log.warning("Chromium browser disconnected. Restarting...")
                cls._chromium = None
            # Check if firefox is dead
            if cls._firefox and not cls._firefox.is_connected():
                log.warning("Firefox browser disconnected. Restarting...")
                cls._firefox = None

            if cls._playwright is None:
                log.info("Starting global Playwright instance...")
                try:
                    cls._playwright = await asyncio.wait_for(async_playwright().start(), timeout=20.0)
                except Exception as e:
                    log.error(f"Failed to start Playwright: {e}", exc_info=True)
                    cls._playwright = None
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
                    cls._chromium = None
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
                    cls._firefox = None
                    raise e

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls._chromium:
                try:
                    await cls._chromium.close()
                except Exception:
                    pass
                cls._chromium = None
            if cls._firefox:
                try:
                    await cls._firefox.close()
                except Exception:
                    pass
                cls._firefox = None
            if cls._playwright:
                try:
                    await cls._playwright.stop()
                except Exception:
                    pass
                cls._playwright = None
                log.info("Playwright stopped.")

    @classmethod
    async def get_browser(cls, browser_type: str = "chromium") -> Browser:
        """Get the active Playwright browser instance, starting it if necessary."""
        await cls.ensure_started(browser_type)
        browser = cls._chromium if browser_type == "chromium" else cls._firefox
        if browser is None or not browser.is_connected():
            # If it died right after ensure_started
            await cls.ensure_started(browser_type)
            browser = cls._chromium if browser_type == "chromium" else cls._firefox
            if browser is None or not browser.is_connected():
                raise RuntimeError(f"{browser_type.capitalize()} Browser failed to initialize or died immediately.")
        return browser

    @classmethod
    @asynccontextmanager
    async def get_context(cls, context_options: dict = None, browser_type: str = "chromium") -> AsyncGenerator[BrowserContext, None]:
        """
        Context manager to acquire a managed Playwright context.
        """
        browser = await cls.get_browser(browser_type)
        opts = context_options or {}
        try:
            context = await browser.new_context(**opts)
        except PlaywrightError as e:
            if "Browser closed" in str(e) or "Target page, context or browser has been closed" in str(e):
                log.warning("Browser was closed during get_context. Retrying...")
                browser = await cls.get_browser(browser_type)
                context = await browser.new_context(**opts)
            else:
                raise e

        try:
            yield context
        finally:
            try:
                await context.close()
            except Exception as e:
                log.debug(f"Error closing context: {e}")

    @classmethod
    @asynccontextmanager
    async def get_page(cls, context_options: dict = None, browser_type: str = "chromium") -> AsyncGenerator[Page, None]:
        """
        Context manager to acquire a managed Playwright page with concurrency bounds.
        Use this instead of launching new browsers.
        browser_type can be "chromium" or "firefox".
        """
        async with cls._semaphore:
            browser = await cls.get_browser(browser_type)
            context = None
            page = None
            try:
                opts = context_options or {}
                try:
                    context = await browser.new_context(**opts)
                    page = await context.new_page()
                except PlaywrightError as e:
                    if "Browser closed" in str(e) or "Target page, context or browser has been closed" in str(e):
                        log.warning("Browser was closed during get_page. Retrying...")
                        browser = await cls.get_browser(browser_type)
                        context = await browser.new_context(**opts)
                        page = await context.new_page()
                    else:
                        raise e
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
