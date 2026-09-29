import asyncio
from app.links import extract_product_id, detect_platform, first_url

test_cases = [
    "https://www.zepto.com/pn/daawat-rozana-super-basmati-rice-medium-grain/pvid/7851f4a9-cab6-4b75-bae2-bcbc43bf0bdb",
    "Check out this product on Zepto!\nhttps://www.zepto.com/pn/daawat-rozana-super-basmati-rice-medium-grain/pvid/7851f4a9-cab6-4b75-bae2-bcbc43bf0bdb",
    "https://www.zepto.com/pn/daawat-rozana-super-basmati-rice-medium-grain/pvid/7851f4a9-cab6-4b75-bae2-bcbc43bf0bdb Check out this product on Zepto!",
    "Check this out: https://blinkit.com/prn/foo/prid/123",
    "Check this out:\nhttps://www.swiggy.com/instamart/item/123",
]

for t in test_cases:
    url = first_url(t)
    print(f"[{url}]")
    print(extract_product_id(t))
