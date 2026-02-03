
import time
from playwright.sync_api import sync_playwright, expect

def run_audit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        # Capture console logs
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        base_url = "http://127.0.0.1:5000"

        print(f"Navigating to {base_url}...")
        try:
            page.goto(base_url)
        except Exception as e:
            print(f"Failed to load page: {e}")
            return

        # 1. Public Portal
        print("Auditing Public Portal...")
        try:
            expect(page.get_by_role("heading", name="E-GoPass RDC")).to_be_visible()
            page.screenshot(path="verification/public_portal.png")
            print("Public Portal OK.")
        except Exception as e:
            print(f"Public Portal verification failed: {e}")
            page.screenshot(path="verification/public_fail.png")

        # 2. Login
        print("Navigating to Login...")
        try:
            # Click the link to login
            page.click("text=Accès Agent / Contrôleur")
            page.wait_for_url("**/login")

            expect(page).to_have_title("Connexion - GO-PASS SGI-GP")
            page.screenshot(path="verification/login_page.png")

            print("Logging in...")
            page.fill("input[name='username']", "admin")
            page.fill("input[name='password']", "admin123")
            page.click("button[type='submit']")

            # Wait for navigation
            page.wait_for_url("**/dashboard/")
            print("Login successful.")
        except Exception as e:
            print(f"Login failed: {e}")
            page.screenshot(path="verification/login_fail.png")
            browser.close()
            return

        # 3. Dashboard
        print("Auditing Dashboard...")
        try:
            expect(page.get_by_role("heading", name="Tableau de bord")).to_be_visible()
            # Check for stats
            page.screenshot(path="verification/dashboard.png")
        except Exception as e:
            print(f"Dashboard verification failed: {e}")
            page.screenshot(path="verification/dashboard_fail.png")

        # 4. Users
        print("Auditing Users...")
        try:
            # Try to find link by href or text
            page.click("a[href*='/users/']")
            page.wait_for_url("**/users/")
            expect(page.get_by_role("heading", name="Gestion des utilisateurs")).to_be_visible()
            page.screenshot(path="verification/users.png")
        except Exception as e:
            print(f"Users verification failed: {e}")
            page.screenshot(path="verification/users_fail.png")

        # 5. Flights
        print("Auditing Flights...")
        try:
            # Navigate back to dashboard or find link
            # Assuming sidebar is always present
            page.click("a[href*='/flights/']")
            page.wait_for_url("**/flights/")
            # expect(page.get_by_role("heading", name="Vols")).to_be_visible()
            page.screenshot(path="verification/flights.png")
        except Exception as e:
            print(f"Flights verification failed: {e}")
            page.screenshot(path="verification/flights_fail.png")

        browser.close()

if __name__ == "__main__":
    run_audit()
