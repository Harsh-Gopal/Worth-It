import tls_client

session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

res = session.get(
    "https://www.zepto.com/search?q=protein",
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
    }
)

print("Status:", res.status_code)
if "challenge.js" in res.text:
    print("BLOCKED BY AWS WAF CHALLENGE!")
else:
    print("SUCCESS!")
    print(res.text[:500])
