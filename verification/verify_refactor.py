from playwright.sync_api import sync_playwright
import time

def verify_refactor():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Public Index
        print("Verifying Public Index...")
        page.goto("http://localhost:5000/")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="verification/public_index.png")
        print("Public Index Screenshot saved.")

        # 2. Login Page
        print("Verifying Login...")
        # Try /login (standard) or /auth/login (if prefixed)
        response = page.goto("http://localhost:5000/login")
        if response.status == 404:
             print("Retrying with /auth/login...")
             page.goto("http://localhost:5000/auth/login")

        page.wait_for_load_state("networkidle")
        page.screenshot(path="verification/login.png")
        print("Login Screenshot saved.")

        # 3. Perform Login
        print("Logging in...")
        page.fill("input[name='username']", "agent")
        page.fill("input[name='password']", "agent123")
        page.click("button[type='submit']")

        # Wait for redirect (Dashboard or POS depending on role)
        # Agent role goes to POS (/ops/pos)
        page.wait_for_load_state("networkidle")
        print(f"Logged in. Current URL: {page.url}")

        # Take screenshot of landing page after login
        page.screenshot(path="verification/after_login.png")

        # 4. Dashboard (Explicit navigation if not redirected there)
        print("Verifying Dashboard...")
        page.goto("http://localhost:5000/dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="verification/dashboard.png")
        print("Dashboard Screenshot saved.")

        # 5. Scanner
        print("Verifying Scanner...")
        page.goto("http://localhost:5000/ops/scanner")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="verification/scanner.png")
        print("Scanner Screenshot saved.")

        browser.close()

if __name__ == "__main__":
    verify_refactor()
