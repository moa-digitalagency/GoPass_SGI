from playwright.sync_api import sync_playwright, expect
import os

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Capture console logs
    page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))

    base_url = "http://127.0.0.1:5000"

    print("Auditing Landing Page...")
    page.goto(base_url + "/")
    page.screenshot(path="verification/landing_page.png")

    print("Auditing Aide Page...")
    page.goto(base_url + "/aide")
    page.screenshot(path="verification/aide_page.png")

    print("Auditing Login...")
    page.goto(base_url + "/login")
    page.screenshot(path="verification/login_page.png")

    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "admin123")
    page.click("button[type='submit']")

    # Wait for dashboard
    try:
        page.wait_for_url("**/dashboard", timeout=5000)
        print("Login Successful. Auditing Dashboard...")
        page.screenshot(path="verification/dashboard.png")
    except Exception as e:
        print(f"Login Failed or Dashboard timeout: {e}")
        page.screenshot(path="verification/login_failed.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
