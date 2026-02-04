from playwright.sync_api import sync_playwright, expect
import os
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # Login
        print("Logging in...")
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")

        # Wait for redirection to complete
        page.wait_for_load_state("networkidle")

        # Navigate to POS
        print("Navigating to POS...")
        page.goto("http://127.0.0.1:5000/ops/pos")

        # Verify elements
        # 1. Header
        print("Verifying Header...")
        expect(page.get_by_text("Guichet N°")).to_be_visible()

        # 2. Split Screen
        # Left: Form
        expect(page.get_by_text("Émission de Titre de Voyage")).to_be_visible()
        # Right: History
        expect(page.get_by_text("Ventes Récentes")).to_be_visible()

        # 3. Flight Mode Toggle
        print("Toggling Manual Mode...")
        page.click("button:has-text('Vol Ultérieur / Manuel')")
        # Check if manual inputs appear
        expect(page.locator("input[name='manual_flight_number']")).to_be_visible()

        # 4. Fill Form (Manual Mode)
        print("Filling Form...")
        page.fill("input[name='manual_flight_date']", "2023-12-25")
        page.fill("input[name='manual_flight_number']", "TEST-999")
        page.fill("input[name='passenger_name']", "Jean Test")
        page.fill("input[name='passenger_passport']", "P123456")

        # 5. Submit
        # Mocking window.print to avoid error if any
        page.evaluate("window.print = function() {};")
        print("Submitting...")
        page.click("#submitBtn")

        # 6. Verify History Update
        print("Verifying History...")
        # Increase timeout for async operation
        expect(page.locator("#history-list")).to_contain_text("Jean Test", timeout=10000)
        expect(page.locator("#history-list")).to_contain_text("TEST-999")

        # Screenshot
        print("Taking screenshot...")
        page.screenshot(path="verification/pos_ui.png", full_page=True)

        browser.close()

if __name__ == "__main__":
    run()
