"""
🌐 Hermes-Agent: Agent-Reach Internet Capability Router (v3.9.0)
Exposes REST endpoints for:
- 15-platform reach status (`/api/reach/status`)
- Zero-cost web scraping via Jina Reader (`/api/reach/read-url`)
- Fast YouTube subtitle & metadata extraction via yt-dlp (`/api/reach/youtube-transcript`)
- RSS / Atom feed parsing (`/api/reach/rss`)
- Autonomous end-to-end ingestion to Omnichannel Drafts (`/api/reach/ingest-to-omnichannel`)
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl

from backend.services.reach_engine import ReachEngine

logger = logging.getLogger("hermes.routers.reach")
router = APIRouter(prefix="/api/reach", tags=["reach"])


class ReadUrlRequest(BaseModel):
    url: str
    timeout: Optional[float] = 15.0


class YouTubeTranscriptRequest(BaseModel):
    url: str
    timeout: Optional[float] = 30.0


class RssFeedRequest(BaseModel):
    url: str
    limit: Optional[int] = 5


class IngestOmnichannelRequest(BaseModel):
    url: str
    source_type: Optional[str] = "auto"
    target_audience: Optional[str] = "Usahawan & Peminat Teknologi / AI"
    language: Optional[str] = "Bahasa Melayu & English"
    tone: Optional[str] = "Berpengaruh, praktikal, santai & berautoriti"
    auto_save: Optional[bool] = True


@router.get("/status")
async def get_reach_status():
    """Returns the live status of Agent-Reach multi-platform backends."""
    try:
        status_data = await ReachEngine.get_status()
        return {"status": "success", "data": status_data}
    except Exception as e:
        logger.error(f"Error fetching reach status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read-url")
async def read_url(req: ReadUrlRequest):
    """Reads any URL via Jina Reader without headless browser overhead."""
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL parameter cannot be empty")
    try:
        result = await ReachEngine.read_url_jina(req.url, timeout=req.timeout or 15.0)
        return result
    except Exception as e:
        logger.error(f"Error reading URL {req.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/youtube-transcript")
async def get_youtube_transcript(req: YouTubeTranscriptRequest):
    """Extracts YouTube subtitles and metadata using yt-dlp."""
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL parameter cannot be empty")
    try:
        result = await ReachEngine.extract_youtube(req.url, timeout=req.timeout or 30.0)
        return result
    except Exception as e:
        logger.error(f"Error extracting YouTube transcript {req.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss")
async def get_rss_feed(req: RssFeedRequest):
    """Parses an RSS or Atom feed."""
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL parameter cannot be empty")
    try:
        result = ReachEngine.read_rss(req.url, limit=req.limit or 5)
        return result
    except Exception as e:
        logger.error(f"Error parsing RSS {req.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-to-omnichannel")
async def ingest_to_omnichannel(req: IngestOmnichannelRequest):
    """End-to-end ingestion pipeline: scrapes URL/video, synthesizes copy, validates, and saves draft."""
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL parameter cannot be empty")
    try:
        result = await ReachEngine.ingest_to_omnichannel(
            url=req.url,
            source_type=req.source_type or "auto",
            target_audience=req.target_audience or "Usahawan & Peminat Teknologi / AI",
            language=req.language or "Bahasa Melayu & English",
            tone=req.tone or "Berpengaruh, praktikal, santai & berautoriti",
            auto_save=req.auto_save if req.auto_save is not None else True,
        )
        return result
    except Exception as e:
        logger.error(f"Error during omnichannel ingestion for {req.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
