import asyncio
from app.platforms.swiggy import _fetch_page, _extract_redux

async def main():
    html = await _fetch_page("F9UK3KLPCI", 25.6075, 85.0830)
    data = _extract_redux(html, "F9UK3KLPCI")
    print("EXTRACTED:", data)
    if not data["store_id"]:
        # Find storeId in HTML manually
        import re
        sid_m = re.search(r'"storeDetailsV2"\s*:\s*\{"storeId"\s*:\s*"(\d+)"', html)
        print("REGEX storeDetailsV2:", sid_m)
        sid2_m = re.findall(r'"storeId"\s*:\s*"(\d+)"', html)
        print("ALL storeIds:", sid2_m)

if __name__ == "__main__":
    asyncio.run(main())
