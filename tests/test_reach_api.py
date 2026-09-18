"""Unit & integration tests for Agent-Reach Internet Capability Router & Ingestion Engine."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.reach_engine import ReachEngine

client = TestClient(app)


def test_reach_status_endpoint():
    """GET /api/reach/status returns live status dictionary with platforms."""
    response = client.get("/api/reach/status")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "platforms" in data["data"]
    platforms = data["data"]["platforms"]
    assert "youtube" in platforms
    assert "web" in platforms


def test_read_url_empty_validation():
    """POST /api/reach/read-url with empty url triggers 400 error."""
    response = client.post("/api/reach/read-url", json={"url": "   "})
    assert response.status_code == 400
    assert "URL parameter cannot be empty" in response.json()["detail"]


def test_read_url_mocked_success(monkeypatch):
    """POST /api/reach/read-url retrieves clean markdown through Jina Reader."""
    mock_result = {
        "status": "success",
        "source": "jina-reader",
        "url": "https://example.com/viral-pastry",
        "title": "Rahsia Donut Bomboloni Viral 2026",
        "word_count": 120,
        "content": "# Rahsia Donut Bomboloni Viral 2026\nKandungan artikel pastri gebu...",
    }

    async def mock_read(*args, **kwargs):
        return mock_result

    monkeypatch.setattr(ReachEngine, "read_url_jina", mock_read)

    response = client.post("/api/reach/read-url", json={"url": "https://example.com/viral-pastry"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["title"] == "Rahsia Donut Bomboloni Viral 2026"
    assert "content" in data


def test_youtube_transcript_empty_validation():
    """POST /api/reach/youtube-transcript with empty url triggers 400 error."""
    response = client.post("/api/reach/youtube-transcript", json={"url": ""})
    assert response.status_code == 400


def test_youtube_transcript_mocked(monkeypatch):
    """POST /api/reach/youtube-transcript returns subtitle and video metadata."""
    mock_result = {
        "status": "success",
        "source": "extracted-subtitles",
        "url": "https://youtube.com/watch?v=mock123",
        "title": "Tutorial Donut Lembut 48 Jam",
        "channel": "Chef Pastri",
        "duration_seconds": 450,
        "has_subtitles": True,
        "transcript": "Mula-mula masukkan tepung dan yis kemudian uli sehingga elastik...",
        "description": "Video cara buat donut gebu...",
        "content": "Mula-mula masukkan tepung dan yis...",
    }

    async def mock_yt(*args, **kwargs):
        return mock_result

    monkeypatch.setattr(ReachEngine, "extract_youtube", mock_yt)

    response = client.post("/api/reach/youtube-transcript", json={"url": "https://youtube.com/watch?v=mock123"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["has_subtitles"] is True
    assert data["title"] == "Tutorial Donut Lembut 48 Jam"


def test_rss_feed_mocked(monkeypatch):
    """POST /api/reach/rss parses feed entries successfully."""
    mock_result = {
        "status": "success",
        "feed_title": "Food Trends Feed",
        "entries_count": 1,
        "entries": [
            {
                "title": "Trend Donut Karamel 2026",
                "link": "https://foodtrends.com/donut-2026",
                "summary": "Karamel leleh menjadi kegilaan ramai...",
                "published": "Wed, 16 Sep 2026 10:00:00 GMT",
            }
        ],
    }

    def mock_parse(*args, **kwargs):
        return mock_result

    monkeypatch.setattr(ReachEngine, "read_rss", mock_parse)

    response = client.post("/api/reach/rss", json={"url": "https://foodtrends.com/feed.xml", "limit": 2})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["entries_count"] == 1


def test_ingest_to_omnichannel_web(monkeypatch):
    """POST /api/reach/ingest-to-omnichannel completes end-to-end ingestion and creates validated draft."""
    mock_web = {
        "status": "success",
        "source": "jina-reader",
        "url": "https://bakingmag.com/trending-buns",
        "title": "Revolusi Pastri Krim Pistachio Terkini",
        "content": "Krim pistachio asli dengan doh sourdough dingin menjadi tumpuan di kafe terkemuka.",
    }

    async def mock_read(*args, **kwargs):
        return mock_web

    monkeypatch.setattr(ReachEngine, "read_url_jina", mock_read)

    payload = {
        "url": "https://bakingmag.com/trending-buns",
        "source_type": "web",
        "target_audience": "Peminat Pastri & Usahawan",
        "auto_save": True,
    }

    response = client.post("/api/reach/ingest-to-omnichannel", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["source_type"] == "web"
    assert data["draft_id"] is not None
    assert "facebook" in data
    assert "instagram" in data
    assert "tiktok" in data
    assert "youtube" in data
    assert "validation" in data
    assert "tiktok" in data["validation"]
    assert data["state"] == "pending_approval"


def test_ingest_to_omnichannel_youtube_auto_detect(monkeypatch):
    """POST /api/reach/ingest-to-omnichannel auto-detects YouTube URL and delegates to extract_youtube."""
    mock_yt = {
        "status": "success",
        "source": "extracted-subtitles",
        "url": "https://www.youtube.com/watch?v=pastry789",
        "title": "Donut Sourdough Viral Lembut",
        "transcript": "Doh ditapai 24 jam sebelum digoreng rangup...",
        "content": "Doh ditapai 24 jam sebelum digoreng rangup...",
    }

    async def mock_extract(*args, **kwargs):
        return mock_yt

    monkeypatch.setattr(ReachEngine, "extract_youtube", mock_extract)

    payload = {
        "url": "https://www.youtube.com/watch?v=pastry789",
        "source_type": "auto",
        "auto_save": True,
    }

    response = client.post("/api/reach/ingest-to-omnichannel", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["source_type"] == "youtube"
    assert data["draft_id"] is not None
    assert data["title"] == "Donut Sourdough Viral Lembut"
