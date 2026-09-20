import asyncio
from app.platforms.swiggy import _fetch_page

async def main():
    html = await _fetch_page("F9UK3KLPCI", 25.6075, 85.0830)
    if not html:
        print("Empty HTML!")
    else:
        print("HTML starts with:", html[:200])
        if "Just a moment" in html:
            print("WAF Challenge Detected!")

if __name__ == "__main__":
    asyncio.run(main())
