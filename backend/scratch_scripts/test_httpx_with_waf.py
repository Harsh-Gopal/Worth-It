import asyncio
import httpx
import urllib.parse
from playwright.async_api import async_playwright

async def get_waf_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
            locale="en-IN", timezone_id="Asia/Kolkata"
        )
        await context.add_cookies([
            {"name": "userLocation", "value": urllib.parse.quote('{"lat":25.6075,"lng":85.0830,"address":"India"}'), "domain": ".swiggy.com", "path": "/"}
        ])
        page = await context.new_page()
        await page.goto("https://www.swiggy.com/instamart", wait_until="domcontentloaded", timeout=60000)
        
        for _ in range(30):
            cookies = await context.cookies()
            cnames = [c["name"] for c in cookies]
            if "aws-waf-token" in cnames and "deviceId" in cnames:
                break
            await asyncio.sleep(1)
        final_cookies = {c["name"]: c["value"] for c in await context.cookies()}
        await browser.close()
        return final_cookies

async def test():
    cookies = await get_waf_cookies()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0',
    }
    
    async with httpx.AsyncClient(timeout=30, cookies=cookies) as client:
        r = await client.get('https://www.swiggy.com/instamart', headers=headers)
        idx = r.text.find('1401272')
        if idx != -1:
            print('FOUND at', idx)
            print(r.text[max(0, idx-50):min(len(r.text), idx+100)])
        else:
            print('NOT FOUND in httpx with WAF cookies')
            
asyncio.run(test())
