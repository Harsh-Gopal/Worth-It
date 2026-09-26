import asyncio
import nodriver as uc

async def main():
    browser = await uc.start(headless=True)
    page = await browser.get("https://www.zepto.com/search?q=protein")
    await asyncio.sleep(4)
    content = await page.get_content()
    
    with open("nodriver_dump.html", "w") as f:
        f.write(content)
    if "product-card" in content or "Let's Try" in content:
        print("FOUND PRODUCTS!")
    else:
        print("NO PRODUCTS.")
    
    await browser.stop()

if __name__ == '__main__':
    # nodriver requires the loop to be handled gracefully
    uc.loop().run_until_complete(main())
