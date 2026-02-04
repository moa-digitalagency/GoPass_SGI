import os
import time
import subprocess
import signal
from playwright.sync_api import sync_playwright

def verify_tickets():
    # Start the Flask app
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['DATABASE_URL'] = 'sqlite:///:memory:'
    env['SESSION_SECRET'] = 'secret'
    env['AVIATIONSTACK_API_KEY'] = 'dummy' # Avoid key error if loaded
    env['TELEGRAM_ENCRYPTION_KEY'] = 'dummy'

    # Check if port 5000 is in use and kill it
    try:
        subprocess.run(['fuser', '-k', '5000/tcp'])
    except:
        pass

    # Using python app.py directly as per app.py content
    process = subprocess.Popen(
        ['python3', 'app.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )

    print("Starting Flask app...")
    time.sleep(10) # Wait for startup

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # Verify A4 Ticket (Landscape)
            print("Navigating to A4 Ticket...")
            try:
                response = page.goto("http://localhost:5000/preview/ticket/a4", timeout=10000)
                if not response.ok:
                    print(f"Error loading A4 Ticket: {response.status}")

                # Wait for content to load
                page.wait_for_selector('h1', timeout=5000)

                # A4 Landscape viewport: 297mm x 210mm -> 1123px x 794px @ 96 DPI
                page.set_viewport_size({"width": 1123, "height": 794})
                page.screenshot(path="verification/ticket_a4.png", full_page=True)
                print("Captured A4 Ticket screenshot.")
            except Exception as e:
                print(f"Failed to capture A4 Ticket: {e}")

            # Verify Thermal Ticket
            print("Navigating to Thermal Ticket...")
            try:
                response = page.goto("http://localhost:5000/preview/ticket/thermal", timeout=10000)
                if not response.ok:
                    print(f"Error loading Thermal Ticket: {response.status}")

                page.wait_for_selector('h1', timeout=5000)

                page.set_viewport_size({"width": 302, "height": 800}) # 80mm approx
                page.screenshot(path="verification/ticket_thermal.png", full_page=True)
                print("Captured Thermal Ticket screenshot.")
            except Exception as e:
                print(f"Failed to capture Thermal Ticket: {e}")

            browser.close()

    finally:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            print("Flask app stopped.")
        except:
            pass

if __name__ == "__main__":
    verify_tickets()
