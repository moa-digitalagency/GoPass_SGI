"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for verify_branding.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from playwright.sync_api import sync_playwright
import time

def verify_branding():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # ---------------------------------------------------------
        # 1. Verify Default State (Mocking NO Logo)
        # ---------------------------------------------------------
        print("Navigating to login page (Default state - MOCKED)...")

        def handle_settings_default(route):
            # print("Intercepted settings request (Default)!")
            route.fulfill(json={
                "gopass_logo": None,
                "rva_logo": None
            })

        # Set up route interception for default state
        page.route("**/api/settings/public", handle_settings_default)

        page.goto("http://127.0.0.1:5000/login")

        # Wait for potential JS execution
        time.sleep(1)

        # Check if Default Title is visible
        # It should be visible because gopass_logo is null
        try:
            page.wait_for_selector("h1#login-default-title", state="visible", timeout=5000)
            print("SUCCESS: Default title visible.")
        except Exception as e:
            print(f"FAILURE: Default title NOT visible. {e}")
            # Debug: Check class list
            cls = page.get_attribute("h1#login-default-title", "class")
            print(f"DEBUG: Title classes: {cls}")

        # Check if RVA logo is absent
        rva_logo = page.query_selector("img[src*='logo_rva.png']")
        if rva_logo:
             print("FAILURE: RVA Logo found!")
        else:
             print("SUCCESS: RVA Logo not found.")

        # ---------------------------------------------------------
        # 2. Verify Branded State (Mocking WITH Logo)
        # ---------------------------------------------------------
        print("\nReloading login page (Branded state - MOCKED)...")

        # Unroute previous handler to be safe, though verifying overwrite works
        page.unroute("**/api/settings/public")

        def handle_settings_branded(route):
            # print("Intercepted settings request (Branded)!")
            route.fulfill(json={
                "gopass_logo": "/static/img/logo_gopass.png",
                "rva_logo": None
            })

        # Set up route interception for branded state
        page.route("**/api/settings/public", handle_settings_branded)

        # Reload to trigger the fetch with the new mocked response
        page.reload()

        # Wait for logic to apply
        time.sleep(1)

        try:
            # wait for logo to have src and be visible
            # Note: base.html JS removes 'hidden' class from #login-logo-gopass
            page.wait_for_selector("#login-logo-gopass:not(.hidden)", timeout=5000)
            print("SUCCESS: GoPass Logo container is visible.")

            # Check if default title is hidden
            # base.html JS adds 'hidden' class to #login-default-title
            title = page.locator("#login-default-title")
            if not title.is_visible():
                print("SUCCESS: Default title is hidden.")
            else:
                print("FAILURE: Default title is STILL visible.")

        except Exception as e:
            print(f"FAILURE in Branded State check: {e}")

        browser.close()

if __name__ == "__main__":
    verify_branding()
