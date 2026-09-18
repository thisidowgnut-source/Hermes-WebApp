import asyncio
import os
import shutil
from playwright.async_api import async_playwright

artifact_dir = r"C:\Users\megat\.gemini\antigravity-cli\brain\23a055a5-105c-4a2d-876e-8e13415b4db4"
static_dir = r"C:\Users\megat\Hermes-WebApp\static"
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.launch(executable_path=chrome_path, headless=True)
    
    # 1. Desktop Dashboard View (1366x850)
    page_desktop = await browser.new_page(viewport={"width": 1366, "height": 850})
    await page_desktop.goto("http://127.0.0.1:9220/", wait_until="domcontentloaded")
    await asyncio.sleep(1.2)
    desktop_png = os.path.join(artifact_dir, "hermes_desktop_dashboard.png")
    await page_desktop.screenshot(path=desktop_png)
    shutil.copyfile(desktop_png, os.path.join(static_dir, "hermes_desktop_dashboard.png"))
    print("[+] Desktop dashboard captured:", desktop_png)
    
    # 2. Open Catalog Modal (16 Modules)
    await page_desktop.evaluate("openModule('appdrawer')")
    await asyncio.sleep(0.6)
    catalog_png = os.path.join(artifact_dir, "hermes_catalog_modal.png")
    await page_desktop.screenshot(path=catalog_png)
    shutil.copyfile(catalog_png, os.path.join(static_dir, "hermes_catalog_modal.png"))
    print("[+] Catalog modal captured:", catalog_png)
    await page_desktop.close()

    # 3. Mobile Viewport (iPhone 14, 390x844)
    page_mobile = await browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
    await page_mobile.goto("http://127.0.0.1:9220/", wait_until="domcontentloaded")
    await asyncio.sleep(1.2)
    mobile_png = os.path.join(artifact_dir, "hermes_mobile_dashboard.png")
    await page_mobile.screenshot(path=mobile_png)
    shutil.copyfile(mobile_png, os.path.join(static_dir, "hermes_mobile_dashboard.png"))
    print("[+] Mobile dashboard captured:", mobile_png)

    # 4. Open Terminal on Mobile
    await page_mobile.evaluate("openModule('terminal')")
    await asyncio.sleep(0.6)
    term_png = os.path.join(artifact_dir, "hermes_terminal_mobile.png")
    await page_mobile.screenshot(path=term_png)
    shutil.copyfile(term_png, os.path.join(static_dir, "hermes_terminal_mobile.png"))
    print("[+] Terminal mobile captured:", term_png)
    await page_mobile.close()

    # 5. Open Vision Node / Browser on Desktop
    page_vision = await browser.new_page(viewport={"width": 1366, "height": 850})
    await page_vision.goto("http://127.0.0.1:9220/", wait_until="domcontentloaded")
    await asyncio.sleep(1.0)
    await page_vision.evaluate("openModule('browser')")
    await asyncio.sleep(0.6)
    vision_png = os.path.join(artifact_dir, "hermes_vision_node.png")
    await page_vision.screenshot(path=vision_png)
    shutil.copyfile(vision_png, os.path.join(static_dir, "hermes_vision_node.png"))
    print("[+] Vision Node captured:", vision_png)
    await page_vision.close()

    await browser.close()
    await p.stop()
    print("[SUCCESS] ALL 5 PREVIEW SCREENSHOTS CAPTURED!")

if __name__ == "__main__":
    asyncio.run(main())
