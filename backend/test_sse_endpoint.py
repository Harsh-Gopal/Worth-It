import asyncio
import httpx
import json

async def main():
    async with httpx.AsyncClient() as client:
        payload = {
            "pincode": "800014",
            "search_mode": "keyword",
            "keyword": "Coconut",
            "match_keywords": ["Coconut"],
            "condition": {
                "min_discount_pct": 50,
                "require_in_stock": True,
                "condition_operator": "AND"
            }
        }
        
        async with client.stream("POST", "http://127.0.0.1:8000/api/search/stream", json=payload) as response:
            print(f"Status: {response.status_code}")
            async for line in response.aiter_lines():
                if line:
                    print(line)

if __name__ == "__main__":
    asyncio.run(main())
