import asyncio
import base64
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from playwright.async_api import async_playwright

router = APIRouter()

# Global browser state
browser_context = None
browser_page = None

@router.websocket("/ws/browser")
async def browser_ws(websocket: WebSocket):
    global browser_context, browser_page
    await websocket.accept()
    
    playwright = None
    browser = None
    stream_task = None
    heartbeat_task = None

    try:
        try:
            playwright = await async_playwright().start()
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ]
            exec_path = next((p for p in chrome_paths if os.path.exists(p)), None)
            if exec_path:
                browser = await playwright.chromium.launch(executable_path=exec_path, headless=True)
            else:
                browser = await playwright.chromium.launch(headless=True)
            
            browser_context = await browser.new_context(
                viewport={"width": 1024, "height": 768},
                device_scale_factor=1
            )
            browser_page = await browser_context.new_page()
            
            # Navigate to a default page
            try:
                await asyncio.wait_for(browser_page.goto("about:blank"), timeout=2.0)
            except Exception:
                pass
        except Exception as init_err:
            print(f"[BrowserWS] Playwright initialization warning: {init_err}")
            browser = None
            browser_context = None
            browser_page = None

        async def stream_screen():
            while True:
                try:
                    if browser_page and not browser_page.is_closed():
                        screenshot = await browser_page.screenshot(type="jpeg", quality=40)
                        b64 = base64.b64encode(screenshot).decode("utf-8")
                        await websocket.send_text(json.dumps({"type": "frame", "data": b64}))
                    await asyncio.sleep(0.2) # 5 FPS to save bandwidth
                except Exception:
                    break

        async def heartbeat():
            while True:
                try:
                    await asyncio.sleep(15)
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break

        if browser_page:
            stream_task = asyncio.create_task(stream_screen())
        heartbeat_task = asyncio.create_task(heartbeat())

        while True:
            data = await websocket.receive_text()
            if data in ("ping", '{"type": "ping"}', '{"type":"ping"}'):
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            elif data in ("pong", '{"type": "pong"}', '{"type":"pong"}'):
                continue

            try:
                cmd = json.loads(data)
            except Exception:
                cmd = {}
            
            cmd_type = cmd.get("type")
            if cmd_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            elif cmd_type == "pong":
                continue
            elif browser_page and not browser_page.is_closed():
                if cmd_type == "click":
                    await browser_page.mouse.click(cmd.get("x", 0), cmd.get("y", 0))
                elif cmd_type == "type":
                    await browser_page.keyboard.type(cmd.get("text", ""))
                elif cmd_type == "keydown":
                    await browser_page.keyboard.press(cmd.get("key", ""))
                elif cmd_type == "goto":
                    try:
                        url = cmd.get("url", "https://google.com")
                        if not url.startswith("http://") and not url.startswith("https://"):
                            url = "https://" + url
                        await browser_page.goto(url)
                    except Exception as e:
                        await websocket.send_text(json.dumps({"type": "error", "msg": str(e)}))
                
    except (WebSocketDisconnect, asyncio.CancelledError, Exception):
        pass
    finally:
        if stream_task:
            stream_task.cancel()
        if heartbeat_task:
            heartbeat_task.cancel()

        if browser_page:
            try:
                if not browser_page.is_closed():
                    await browser_page.close()
            except Exception:
                pass
            browser_page = None

        if browser_context:
            try:
                await browser_context.close()
            except Exception:
                pass
            browser_context = None

        if browser:
            try:
                await browser.close()
            except Exception:
                pass

        if playwright:
            try:
                await playwright.stop()
            except Exception:
                pass

