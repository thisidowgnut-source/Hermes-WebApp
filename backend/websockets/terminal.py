import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/terminal")
async def terminal_ws(websocket: WebSocket):
    await websocket.accept()
    process = await asyncio.create_subprocess_exec(
        "pwsh.exe", "-NoProfile", "-NoLogo",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=r"C:\Users\megat"
    )

    async def read_stdout():
        while True:
            try:
                data = await process.stdout.read(1024)
                if not data:
                    break
                await websocket.send_text(data.decode("utf-8", errors="replace"))
            except Exception:
                break

    async def heartbeat():
        while True:
            try:
                await asyncio.sleep(15)
                # Send quiet WebSocket ping frame instead of text JSON that leaks into xterm stdout
                await websocket.send_bytes(b"\x09")
            except Exception:
                break

    task = asyncio.create_task(read_stdout())
    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            data = await websocket.receive_text()
            if data in ("ping", '{"type": "ping"}', '{"type":"ping"}'):
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            elif data in ("pong", '{"type": "pong"}', '{"type":"pong"}'):
                continue

            if process.stdin and not process.stdin.is_closing():
                # Forward raw data to pwsh. xterm.js sends \r for Enter.
                # pwsh.exe pipe mode needs \r\n to execute a command.
                if data == "\r":
                    process.stdin.write(b"\r\n")
                elif data == "\x03":
                    process.stdin.write(b"\x03")  # Ctrl+C
                elif data == "\x1a":
                    process.stdin.write(b"\x1a")  # Ctrl+Z
                elif data == "\x0c":
                    process.stdin.write(b"\x0c")  # Ctrl+L (clear)
                else:
                    normalized = data.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
                    process.stdin.write(normalized.encode("utf-8"))
                await process.stdin.drain()
    except (WebSocketDisconnect, asyncio.CancelledError, Exception):
        pass
    finally:
        heartbeat_task.cancel()
        task.cancel()
        if process and process.returncode is None:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

