import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.audio_engine import audio_engine

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/audio")
async def audio_ws(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(json.dumps({
        "type": "connection_established",
        "status": "ready",
        "msg": "Audio WebSocket Connected"
    }))

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                pcm_bytes = message["bytes"]
                vad_result = audio_engine.detect_vad(pcm_bytes)
                stem_result = audio_engine.process_stem(pcm_bytes)

                response_frame = {
                    "type": "audio_telemetry",
                    "status": "success",
                    "speech_transcript": "Voice CLI Command Received",
                    "transcript": "Voice CLI Command Received",
                    "vad": vad_result,
                    "stems": stem_result["stems"],
                    "spectrum": stem_result["spectrum"],
                    "data": {
                        "text": "Voice CLI Command Received",
                        "command": None,
                        "bytes_received": len(pcm_bytes)
                    }
                }
                await websocket.send_text(json.dumps(response_frame))
            elif "text" in message and message["text"]:
                data = message["text"]
                if data in ("ping", '{"type": "ping"}', '{"type":"ping"}'):
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    continue
                elif data in ("pong", '{"type": "pong"}', '{"type":"pong"}'):
                    continue

                try:
                    payload = json.loads(data)
                    msg_type = payload.get("type") or payload.get("action")
                    if msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif msg_type == "set_vad":
                        thresh = payload.get("threshold", 0.02)
                        new_t = audio_engine.set_vad_threshold(thresh)
                        await websocket.send_text(json.dumps({
                            "type": "vad_updated",
                            "threshold": new_t,
                            "vad_threshold": new_t
                        }))
                    elif msg_type == "simulate_speech":
                        text = payload.get("text", "")
                        cmd_res = audio_engine.parse_command(text)
                        await websocket.send_text(json.dumps({
                            "type": "voice_command",
                            "matched": cmd_res["matched"],
                            "voice_command": cmd_res
                        }))
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
    except (WebSocketDisconnect, asyncio.CancelledError, Exception):
        pass
