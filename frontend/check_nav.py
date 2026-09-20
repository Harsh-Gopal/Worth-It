from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        try:
            print("Navigating to / (Monitor)")
            page.goto("http://localhost:5173", wait_until="networkidle")
            time.sleep(1)
            
            print("Navigating to /history")
            page.evaluate("window.history.pushState(null, '', '/history'); window.dispatchEvent(new Event('popstate'));")
            time.sleep(1)
            
            print("Navigating back to /")
            page.evaluate("window.history.pushState(null, '', '/'); window.dispatchEvent(new Event('popstate'));")
            time.sleep(1)
            
            print("Done navigating")
        except Exception as e:
            print(f"Error loading page: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
