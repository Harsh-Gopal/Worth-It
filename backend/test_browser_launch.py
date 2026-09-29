import asyncio
from app.core.browser import BrowserManager
from app.config import get_settings

async def test_browser():
    settings = get_settings()
    print(f"Playwright Enabled: {settings.playwright_enabled}")
    if not settings.playwright_enabled:
        print("Playwright is not enabled by config.")
        return

    try:
        print("Ensuring browser is started...")
        await BrowserManager.ensure_started("chromium")
        print("Browser started.")
        
        async with BrowserManager.get_page(browser_type="chromium") as page:
            print("Page created successfully.")
            await page.goto("about:blank")
            content = await page.content()
            print(f"Page content length: {len(content)}")
            
        print("Browser launch: successful")
    except Exception as e:
        print(f"Browser launch failed: {e}")
    finally:
        await BrowserManager.close()

if __name__ == "__main__":
    asyncio.run(test_browser())
