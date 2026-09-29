import asyncio
from fastapi import FastAPI
from app.api.routers.product_url import parse_product_url

async def test():
    url = "Check out this product on Zepto!\nhttps://www.zepto.com/pn/daawat-rozana-super-basmati-rice-medium-grain/pvid/7851f4a9-cab6-4b75-bae2-bcbc43bf0bdb"
    try:
        res = await parse_product_url(url=url)
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
