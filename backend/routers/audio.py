import base64
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from backend.services.audio_engine import audio_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audio", tags=["Audio Engine"])

class SetVadRequest(BaseModel):
    threshold: float

@router.get("/status")
def get_audio_status():
    """
    Returns audio engine telemetry, VAD threshold, and supported stems.
    """
    return {
        "status": "success",
        "data": audio_engine.get_status()
    }

@router.post("/process-stem")
async def process_stem(request: Request):
    """
    Processes audio clip through STEM demux frequency filter processing (Vocals, Drums, Bass, Other).
    Accepts JSON body with audio_base64 or multipart file upload.
    """
    pcm_bytes = b""
    sample_rate = 16000

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                b64_data = body.get("audio_base64")
                if b64_data:
                    pcm_bytes = base64.b64decode(b64_data)
                sample_rate = int(body.get("sample_rate", 16000))
                vad_thresh = body.get("vad_threshold")
                if vad_thresh is not None:
                    audio_engine.set_vad_threshold(float(vad_thresh))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON audio payload: {str(e)}")

    elif "multipart/form-data" in content_type:
        try:
            form = await request.form()
            if "file" in form:
                upload_file = form["file"]
                if hasattr(upload_file, "read"):
                    pcm_bytes = await upload_file.read()
            elif "audio_base64" in form:
                pcm_bytes = base64.b64decode(form["audio_base64"])
        except Exception:
            pass
    else:
        raw_body = await request.body()
        if raw_body:
            pcm_bytes = raw_body

    if not pcm_bytes:
        raise HTTPException(status_code=400, detail="No audio data provided in file or audio_base64 field.")

    vad_result = audio_engine.detect_vad(pcm_bytes)
    stem_result = audio_engine.process_stem(pcm_bytes, sample_rate=sample_rate)

    return {
        "status": "success",
        "vad": vad_result,
        "stems": stem_result["stems"],
        "spectrum": stem_result["spectrum"],
        "sample_rate": sample_rate,
        "bytes_processed": len(pcm_bytes)
    }

@router.post("/vad-threshold")
def set_vad_threshold(req: SetVadRequest):
    """
    Updates VAD sensitivity threshold.
    """
    new_threshold = audio_engine.set_vad_threshold(req.threshold)
    return {
        "status": "success",
        "vad_threshold": float(new_threshold)
    }

@router.post("/parse-command")
async def parse_voice_command(request: Request):
    """
    Parses voice command intent from transcript string.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = body.get("text", "") if isinstance(body, dict) else ""
    result = audio_engine.parse_command(text)
    return {
        "status": "success",
        "result": result
    }
