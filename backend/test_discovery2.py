import asyncio
from app.domain.services.product_discovery import ProductDiscoveryEngine

async def main():
    engine = ProductDiscoveryEngine(None, "") # Empty storeId
    payload = await engine._fetch_search_playwright("Coconut")
    print("PAYLOAD KEYS:", payload.keys())
    if "data" in payload:
        cards = payload["data"].get("cards", [])
        print("NUM CARDS:", len(cards))
    else:
        print("PAYLOAD:", payload)

if __name__ == "__main__":
    asyncio.run(main())
