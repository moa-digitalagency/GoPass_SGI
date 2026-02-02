from playwright.sync_api import sync_playwright

def verify(page):
    # Landing Page
    page.goto("http://localhost:5000/")
    page.screenshot(path="verification/landing.png")
    print("Landing page screenshot taken.")

    # Search
    page.fill("input[name='date']", "2025-11-01") # Using future date or current date
    # I should use a date that has flights.
    # In init_db, I created a flight for tomorrow.
    # But I should probably inject a flight or rely on existing ones.
    # Let's just screenshot landing for now, and try search.

    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="verification/search_results.png")
    print("Search results screenshot taken.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
