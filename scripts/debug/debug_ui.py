import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(f"PAGE ERROR: {exc}"))

        print("Navigating to http://127.0.0.1:9230...")
        await page.goto("http://127.0.0.1:9230", wait_until="networkidle")
        
        # Click all buttons
        buttons = await page.locator("button").all()
        print(f"Found {len(buttons)} buttons. Clicking them...")
        
        for i, btn in enumerate(buttons):
            try:
                # Need to force click if covered or offscreen
                await btn.click(force=True, timeout=500)
                await asyncio.sleep(0.1) # wait for any sync error
            except Exception as e:
                errors.append(f"Button {i} click failed: {str(e)}")
        
        await asyncio.sleep(1) # wait for async errors
        
        if errors:
            print("--- UI ERRORS FOUND ---")
            for e in errors:
                print(e)
        else:
            print("--- NO UI ERRORS FOUND ---")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
