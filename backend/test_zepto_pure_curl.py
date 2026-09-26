import asyncio
import sys
from curl_cffi.requests import AsyncSession

async def main():
    print("Testing curl_cffi GET to zeptonow.com...")
    # impersonate chrome110 is supported by default usually
    async with AsyncSession(impersonate="chrome110") as client:
        # Step 1: GET homepage to get cookies
        resp = await client.get("https://www.zeptonow.com/")
        print("Status:", resp.status_code)
        cookies = client.cookies.get_dict()
        print("Cookies:", list(cookies.keys()))
        
        if "aws-waf-token" in cookies:
            print("Successfully got AWS WAF token without Playwright!!")
        else:
            print("No WAF token.")
            
        if "serviceability" in cookies:
            print("Got serviceability cookie!")

asyncio.run(main())
