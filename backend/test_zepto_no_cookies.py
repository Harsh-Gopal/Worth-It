import asyncio
import httpx
import sys

async def main():
    print("Testing httpx to Zepto BFF without cookies...")
    
    headers = {
        "platform": "ANDROID",
        "tenant": "ZEPTO",
        "appversion": "17.0.1",
        "app_version": "17.0.1",
        "Content-Type": "application/json",
        "User-Agent": "Zepto/17.0.1 (Android; 13)",
        # Use random store UUID
        "store_id": "5ec071fd-78df-41f6-b3ae-7298d9f96a3d",
        "storeid": "5ec071fd-78df-41f6-b3ae-7298d9f96a3d"
    }
    
    body = {
        "query": "protein",
        "pageNumber": 0,
        "mode": "SHOW_ALL_RESULTS"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://bff-gateway.zepto.com/user-search-service/api/v3/search",
            headers=headers,
            json=body
        )
        print("Status:", resp.status_code)
        print("Response:", resp.text[:200])

asyncio.run(main())
