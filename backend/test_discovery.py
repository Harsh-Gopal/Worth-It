import asyncio
import httpx
from app.domain.services.product_discovery import ProductDiscoveryEngine

async def main():
    engine = ProductDiscoveryEngine(None, "e6b72a44-df9b-4ffc-8515-d72b21c97a51") # storeId for Patna 800014 (or any valid)
    payload = await engine._fetch_search_playwright("Coconut")
    print("PAYLOAD KEYS:", payload.keys())
    if "data" in payload:
        cards = payload["data"].get("cards", [])
        print("NUM CARDS:", len(cards))
        for card in cards:
            inner = card.get("card", {}).get("card", {})
            grid = inner.get("gridElements", {}).get("infoWithStyle", {})
            items = grid.get("items", [])
            if items:
                print(f"FOUND {len(items)} ITEMS in a grid")
                print("FIRST ITEM KEYS:", items[0].keys())
                if "item" in items[0]:
                    print("ITEM DETAILS:", items[0]["item"].keys())
                break
    else:
        print("NO DATA IN PAYLOAD:", payload)

    products = engine._parse_products(payload)
    print("PARSED PRODUCTS:", len(products))

if __name__ == "__main__":
    asyncio.run(main())
