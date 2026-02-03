from playwright.sync_api import sync_playwright

def verify_admin(page):
    try:
        # Login
        print("Navigating to Login Page...")
        page.goto("http://localhost:5000/login", timeout=10000)

        print("Filling login credentials...")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")

        print("Submitting login form...")
        page.click("button[type='submit']")

        # Wait for dashboard
        print("Waiting for Dashboard...")
        # Expecting redirection to /dashboard
        page.wait_for_url("**/dashboard/", timeout=10000)

        # Wait for a sidebar or chart to ensure content is loaded
        # Based on file list, dashboard likely has specific structure
        # Just waiting for body for now or h1
        page.wait_for_load_state("networkidle")

        print("Dashboard loaded. Taking screenshot...")
        page.screenshot(path="verification/admin_dashboard.png")
        print("Admin dashboard screenshot taken.")

    except Exception as e:
        print(f"Error: {e}")
        import subprocess
        result = subprocess.run(["cat", "app.log"], capture_output=True, text=True)
        print("App Log:")
        print(result.stdout)
        # Capture screenshot of where we failed
        page.screenshot(path="verification/error_state.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        verify_admin(page)
        browser.close()
