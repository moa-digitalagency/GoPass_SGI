import os
import time
import threading
import multiprocessing
import sys
from flask import Flask
from playwright.sync_api import sync_playwright

# Add repo root to path
sys.path.append(os.getcwd())

from app import create_app
from models import db, Flight, GoPass

# Configuration
PORT = 5001
BASE_URL = f"http://localhost:{PORT}"
SCREENSHOT_DIR = "docs/screenshots"

def run_app():
    os.environ['DATABASE_URL'] = f"sqlite:///{os.path.abspath('instance/gopass.db')}"
    os.environ['SESSION_SECRET'] = "screenshot_secret"
    os.environ['FLASK_ENV'] = "development"

    app = create_app('development')
    app.run(port=PORT, use_reloader=False)

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print(f"Waiting for app to start at {BASE_URL}...")
        # Simple wait loop
        for _ in range(30):
            try:
                page.goto(BASE_URL)
                break
            except:
                time.sleep(1)
        else:
            print("App failed to start.")
            return

        print("App started. Taking screenshots...")

        # 1. Landing Page
        page.goto(f"{BASE_URL}/")
        page.screenshot(path=f"{SCREENSHOT_DIR}/01_landing_page.png", full_page=True)
        print("Captured Landing Page")

        # 2. Login Page
        page.goto(f"{BASE_URL}/login")
        page.screenshot(path=f"{SCREENSHOT_DIR}/02_login_page.png", full_page=True)
        print("Captured Login Page")

        # 3. Help Page
        page.goto(f"{BASE_URL}/aide")
        page.screenshot(path=f"{SCREENSHOT_DIR}/03_help_page.png", full_page=True)
        print("Captured Help Page")

        # 4. Search Page (Public)
        page.goto(f"{BASE_URL}/search")
        page.screenshot(path=f"{SCREENSHOT_DIR}/04_search_page.png", full_page=True)
        print("Captured Search Page")

        # Get a flight ID from DB
        app = create_app('development')
        with app.app_context():
            flight = Flight.query.first()
            flight_id = flight.id if flight else 1

            gopass = GoPass.query.first()
            batch_ref = gopass.payment_ref if gopass else "REF123"

        # 5. Checkout Page
        page.goto(f"{BASE_URL}/checkout/{flight_id}")
        page.screenshot(path=f"{SCREENSHOT_DIR}/05_checkout_page.png", full_page=True)
        print(f"Captured Checkout Page (Flight {flight_id})")

        # 6. Confirmation Page
        page.goto(f"{BASE_URL}/confirmation/batch/{batch_ref}")
        page.screenshot(path=f"{SCREENSHOT_DIR}/06_confirmation_page.png", full_page=True)
        print(f"Captured Confirmation Page (Ref {batch_ref})")

        # 7. Ticket Preview A4
        page.goto(f"{BASE_URL}/preview/ticket/a4")
        page.screenshot(path=f"{SCREENSHOT_DIR}/07_ticket_a4.png", full_page=True)
        print("Captured Ticket A4")

        # 8. Ticket Preview Thermal
        # Thermal is narrow, so we adjust viewport
        thermal_page = context.new_page()
        thermal_page.set_viewport_size({"width": 350, "height": 800}) # approx 80mm
        thermal_page.goto(f"{BASE_URL}/preview/ticket/thermal")
        thermal_page.screenshot(path=f"{SCREENSHOT_DIR}/08_ticket_thermal.png", full_page=True)
        thermal_page.close()
        print("Captured Ticket Thermal")

        # 9. Admin Panel Pages (Submenus)
        print("Starting Admin Panel capture...")
        page.goto(f"{BASE_URL}/logout") # Ensure clean state
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')

        try:
            page.wait_for_url(lambda url: "dashboard" in url, timeout=10000)
            page.wait_for_load_state('networkidle')
            print("Logged in as Admin.")

            admin_pages = [
                ("/dashboard", "09_admin_01_dashboard.png"),
                ("/reports", "09_admin_02_reports.png"),
                ("/reports/anomalies", "09_admin_03_anomalies.png"),
                ("/flights", "09_admin_04_flights.png"),
                ("/finance/transactions", "09_admin_05_finance_transactions.png"),
                ("/finance/deposits", "09_admin_06_finance_deposits.png"),
                ("/finance/reconciliation", "09_admin_07_finance_reconciliation.png"),
                ("/dashboard/telegram", "09_admin_08_telegram_config.png"),
                ("/settings/tariffs", "09_admin_09_settings_tariffs.png"),
                ("/settings/airports", "09_admin_10_settings_airports.png"),
                ("/settings/airlines", "09_admin_11_settings_airlines.png"),
                ("/infrastructure/devices", "09_admin_12_infra_devices.png"),
                ("/infrastructure/printers", "09_admin_13_infra_printers.png"),
                ("/infrastructure/security-keys", "09_admin_14_infra_keys.png"),
                ("/users", "09_admin_15_users.png"),
            ]

            for path, filename in admin_pages:
                url = f"{BASE_URL}{path}"
                print(f"Navigating to {url}...")
                page.goto(url)
                # Wait a bit for charts/tables to render if needed
                page.wait_for_load_state('networkidle')
                page.screenshot(path=f"{SCREENSHOT_DIR}/{filename}", full_page=True)
                print(f"Captured {filename}")

        except Exception as e:
            print(f"Failed during Admin Panel capture: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/09_admin_error.png", full_page=True)

        # Logout
        page.goto(f"{BASE_URL}/logout")

        # 10. POS (Agent)
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', 'agent')
        page.fill('input[name="password"]', 'agent123')
        page.click('button[type="submit"]')
        # Agent redirects to /ops/pos
        try:
            page.wait_for_url(lambda url: "ops/pos" in url, timeout=10000)
            page.wait_for_load_state('networkidle')
            page.screenshot(path=f"{SCREENSHOT_DIR}/10_agent_pos.png", full_page=True)
            print("Captured Agent POS")
        except Exception as e:
            print(f"Failed to capture Agent POS: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/10_agent_pos_error.png", full_page=True)

        browser.close()

if __name__ == "__main__":
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

    server = multiprocessing.Process(target=run_app)
    server.start()

    try:
        take_screenshots()
    finally:
        server.terminate()
        server.join()
