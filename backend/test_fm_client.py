import asyncio
from app.platforms.flipkart import FlipkartMinutesClient

async def main():
    client = FlipkartMinutesClient()
    # Yogabar Protein Bars PID: PSLGZM9QGM99XPZA
    pid = "PSLGZM9QGM99XPZA"
    lat, lng = 12.9716, 77.5946 # Bangalore (serviceable for sure)
    
    print(f"Testing FlipkartMinutesClient for {pid} at {lat}, {lng}...")
    res = await client.product_at_location(pid, lat, lng)
    print("Result:", res)
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
