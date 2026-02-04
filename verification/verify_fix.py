from playwright.sync_api import sync_playwright, expect
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Landing Page
        print("Navigating to landing page...")
        try:
            page.goto("http://localhost:5000/")
            expect(page).to_have_title("GO-PASS SGI-GP")

            # Check logo presence (Footer RVA section has one)
            # Selector: .bg-gray-900 img
            logo = page.locator("section.bg-gray-900 img")
            expect(logo).to_be_visible()

            page.screenshot(path="verification/landing_fixed.png")
            print("Landing page screenshot saved.")
        except Exception as e:
            print(f"Landing page failed: {e}")

        # 2. Login & Dashboard
        print("Navigating to login...")
        try:
            page.goto("http://localhost:5000/auth/login")

            page.fill("input[name='username']", "admin")
            page.fill("input[name='password']", "admin123")
            page.click("button[type='submit']")

            # Wait for dashboard
            # expect(page).to_have_url("http://localhost:5000/dashboard/")
            # Just wait for element
            expect(page.locator("h2:has-text('Tableau de Bord')")).to_be_visible()

            # Check logo in sidebar
            sidebar_logo = page.locator("aside img[alt='RVA']")
            expect(sidebar_logo).to_be_visible()

            page.screenshot(path="verification/dashboard_fixed.png")
            print("Dashboard screenshot saved.")
        except Exception as e:
            print(f"Dashboard failed: {e}")

        browser.close()

if __name__ == "__main__":
    os.makedirs("verification", exist_ok=True)
    run()
