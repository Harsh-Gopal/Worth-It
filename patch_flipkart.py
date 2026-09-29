import sys

with open("backend/app/platforms/flipkart.py", "r") as f:
    content = f.read()

content = content.replace("from .blinkit import _get_browser", "from app.core.browser import BrowserManager")

# normal flipkart
old_product_at_location = """    async def product_at_location(self, product_id: str, lat: float, lng: float) -> ProductResult:
        \"\"\"Fetch price from normal Flipkart. Location not required for stock status.\"\"\"
        browser = await _get_browser()
        context = await browser.new_context(user_agent=_UA)
        page = await context.new_page()
        url = f"https://www.flipkart.com/product/p/itme?pid={product_id}&marketplace=FLIPKART"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)
            result = await page.evaluate(_LD_JSON_JS)
            if result and result.get("price"):
                return ProductResult(
                    status="in_stock",
                    price=result["price"],
                    mrp=result["price"],
                    name=result.get("name"),
                    brand=result.get("brand"),
                    image_url=result.get("image"),
                )
            return ProductResult(status="not_carried")
        except Exception as e:
            log.warning("Flipkart normal extraction failed: %s", e)
            return ProductResult(status="error")
        finally:
            await context.close()"""

new_product_at_location = """    async def product_at_location(self, product_id: str, lat: float, lng: float) -> ProductResult:
        \"\"\"Fetch price from normal Flipkart. Location not required for stock status.\"\"\"
        url = f"https://www.flipkart.com/product/p/itme?pid={product_id}&marketplace=FLIPKART"
        try:
            async with BrowserManager.get_page({"user_agent": _UA}) as page:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)
                result = await page.evaluate(_LD_JSON_JS)
                if result and result.get("price"):
                    return ProductResult(
                        status="in_stock",
                        price=result["price"],
                        mrp=result["price"],
                        name=result.get("name"),
                        brand=result.get("brand"),
                        image_url=result.get("image"),
                    )
                return ProductResult(status="not_carried")
        except Exception as e:
            log.warning("Flipkart normal extraction failed: %s", e)
            return ProductResult(status="error")"""
content = content.replace(old_product_at_location, new_product_at_location)

old_resolve = """        browser = await _get_browser()
        
        # If no product ID is given (e.g. initial discovery sweep), test serviceability via the homepage
        test_url = f"https://www.flipkart.com/product/p/itme?pid={product_id}&marketplace=HYPERLOCAL" if product_id else "https://www.flipkart.com/?marketplace=HYPERLOCAL"

        async with self._sem:
            # ── Strategy 1: GPS injection + wait_for_url navigation ───────────────
            ctx = await browser.new_context(
                user_agent=_UA,
                geolocation={"longitude": lng, "latitude": lat},
                permissions=["geolocation"],
            )
            page = await ctx.new_page()
            try:"""

new_resolve = """        # If no product ID is given (e.g. initial discovery sweep), test serviceability via the homepage
        test_url = f"https://www.flipkart.com/product/p/itme?pid={product_id}&marketplace=HYPERLOCAL" if product_id else "https://www.flipkart.com/?marketplace=HYPERLOCAL"

        async with self._sem:
            # ── Strategy 1: GPS injection + wait_for_url navigation ───────────────
            ctx_opts = {
                "user_agent": _UA,
                "geolocation": {"longitude": lng, "latitude": lat},
                "permissions": ["geolocation"]
            }
            try:
                async with BrowserManager.get_page(ctx_opts) as page:"""

content = content.replace(old_resolve, new_resolve)
# Need to fix the finally block of resolve_store
old_resolve_finally = """            except Exception as e:
                log.warning("Flipkart Minutes extraction failed: %s", e)
                raise PlatformError(f"Flipkart Minutes error: {e}")
            finally:
                await ctx.close()"""

new_resolve_finally = """            except Exception as e:
                log.warning("Flipkart Minutes extraction failed: %s", e)
                from .base import PlatformError
                raise PlatformError(f"Flipkart Minutes error: {e}")"""

content = content.replace(old_resolve_finally, new_resolve_finally)

old_search = """        browser = await _get_browser()
        search_url = f"https://www.flipkart.com/search?q={query}&marketplace=HYPERLOCAL"
        
        products = []
        captured_responses = []

        async def handle_response(response):
            if "api/4/page/fetch" in response.url:
                try:
                    data = await response.json()
                    captured_responses.append(data)
                except Exception:
                    pass

        async with self._sem:
            ctx = await browser.new_context(
                user_agent=_UA,
                geolocation={"longitude": lng, "latitude": lat},
                permissions=["geolocation"],
            )
            page = await ctx.new_page()
            page.on("response", handle_response)
            
            try:"""
new_search = """        search_url = f"https://www.flipkart.com/search?q={query}&marketplace=HYPERLOCAL"
        
        products = []
        captured_responses = []

        async def handle_response(response):
            if "api/4/page/fetch" in response.url:
                try:
                    data = await response.json()
                    captured_responses.append(data)
                except Exception:
                    pass

        async with self._sem:
            ctx_opts = {
                "user_agent": _UA,
                "geolocation": {"longitude": lng, "latitude": lat},
                "permissions": ["geolocation"]
            }
            try:
                async with BrowserManager.get_page(ctx_opts) as page:
                    page.on("response", handle_response)
            """
content = content.replace(old_search, new_search)

old_search_finally = """            except Exception as e:
                log.warning("Flipkart Minutes search failed: %s", e)
            finally:
                await ctx.close()"""
new_search_finally = """            except Exception as e:
                log.warning("Flipkart Minutes search failed: %s", e)"""
content = content.replace(old_search_finally, new_search_finally)

with open("backend/app/platforms/flipkart.py", "w") as f:
    f.write(content)

