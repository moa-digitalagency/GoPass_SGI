from playwright.sync_api import sync_playwright
import time

def verify_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:5000/login", timeout=10000)

            # Take screenshot of login page
            page.screenshot(path="verification/login_page.png")
            print("Screenshot taken.")

            # Check if CSRF token is present in DOM
            token_count = page.locator('input[name="csrf_token"]').count()
            if token_count > 0:
                print("CSRF Token found!")
                # Get the value
                val = page.locator('input[name="csrf_token"]').first.get_attribute("value")
                print(f"Token value: {val[:10]}...")
            else:
                print("CSRF Token NOT found!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_login()
