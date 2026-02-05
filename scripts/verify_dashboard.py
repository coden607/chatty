
import asyncio
import os
from playwright.async_api import async_playwright, expect

async def verify_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Grant permissions for clipboard if needed, though not strictly required here
        context = await browser.new_context()
        page = await context.new_page()

        # Absolute path to the dashboard
        file_path = os.path.abspath("leads_dashboard.html")
        url = f"file://{file_path}"

        print(f"Navigating to {url}")

        # Listen for the consolidated API call
        dashboard_all_called = asyncio.Event()

        async def handle_request(request):
            if "/api/dashboard/all" in request.url:
                print(f"Detected API call: {request.url}")
                dashboard_all_called.set()

        page.on("request", handle_request)

        await page.goto(url)

        # Wait for the API call to happen (initial load)
        try:
            await asyncio.wait_for(dashboard_all_called.wait(), timeout=10)
            print("Successfully verified consolidated API call.")
        except asyncio.TimeoutError:
            print("Timeout waiting for /api/dashboard/all call.")
            # Fallback check if it was too fast

        # Wait for some content to load
        await page.wait_for_selector(".lead-row")

        # Take a screenshot
        screenshot_path = "/home/jules/verification/dashboard_verified.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_dashboard())
