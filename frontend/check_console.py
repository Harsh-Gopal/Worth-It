from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Listen to console events
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        try:
            page.goto("http://localhost:5173", wait_until="networkidle")
        except Exception as e:
            print(f"Error loading page: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
