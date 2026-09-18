"""Integration tests for Doh-Nut Viral & FYP Engine and Durable Scheduler REST API."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.durable_scheduler import get_durable_scheduler

client = TestClient(app)


def test_viral_score_endpoint_low_score():
    """Generic corporate text receives low viral score and recommendations."""
    payload = {"text": "Kami menjual donut berkualiti tinggi dengan harga berpatutan. Sila hubungi kami."}
    response = client.post("/api/social/viral-score", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "total_score" in data
    assert data["total_score"] < 60
    assert data["is_fyp_ready"] is False
    assert len(data["suggestions"]) > 0


def test_viral_score_endpoint_ka_formula():
    """Khairul Aming structured text receives high score and FYP ready status."""
    ka_text = (
        "Ramai yang tanya kenapa donut kitorang tak pernah kempis lepas sejuk. "
        "Rahsia dia kami uli 48 jam guna mentega asli sampai doh lembut macam kapas. "
        "Bila dipotong dua, dengar kerak rangup berderap dengan limpahan leleh karamel panas berasap yang pekat. "
        "Batch petang ni kita goreng 50 kotak je panas-panas, siapa cepat dia dapat. "
        "Korang team Kuih Burger donut atau team Matcha White Choco?"
    )
    response = client.post("/api/social/viral-score", json={"text": ka_text})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_score"] >= 85
    assert data["is_fyp_ready"] is True


def test_generate_ka_campaign_endpoint():
    """Endpoint generates 4-phase Khairul Aming campaign with viral score >= 85."""
    payload = {
        "product_name": "Doh-Nut Karamel Berderap",
        "key_feature": "doh uli 48 jam gebu",
        "arc_type": "struggle_mastery",
    }
    response = client.post("/api/social/generate-ka", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "hook_3s" in data
    assert "story_relatable" in data
    assert "climax_asmr" in data
    assert "organic_scarcity_cta" in data
    assert "full_caption" in data
    assert "viral_score" in data
    assert data["viral_score"]["total_score"] >= 85


def test_validate_post_endpoint_tiktok_aspect_ratio_error():
    """TikTok rejects horizontal aspect ratio and requires 9:16."""
    payload = {
        "platform": "tiktok",
        "text": "Donut sedap gebu #DohNut",
        "media_aspect_ratio": "16:9",
    }
    response = client.post("/api/social/validate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["valid"] is False
    assert any("9:16" in err for err in data["errors"])


def test_validate_post_endpoint_x_autotrim():
    """X post exceeding 280 characters fails validation and provides auto-trim."""
    payload = {
        "platform": "x",
        "text": "Donut gebu sedap uli mentega karamel leleh rangup berderap panas berasap. " * 10,
    }
    response = client.post("/api/social/validate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["valid"] is False
    assert data["auto_trimmed_text"] is not None
    assert len(data["auto_trimmed_text"]) <= 280


def test_schedule_requires_auth_and_csrf():
    """Scheduling a job requires operator session and CSRF header."""
    future_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    payload = {
        "project_slug": "doh-nut",
        "platform": "tiktok",
        "action": "publish_post",
        "payload": {"text": "Viral donut video"},
        "execute_at": future_time,
    }
    # Missing session and CSRF
    resp = client.post("/api/social/schedule", json=payload)
    assert resp.status_code in (401, 403)


def test_schedule_and_manage_jobs_lifecycle(authenticated_session):
    """Authenticated operator can schedule, list, and cancel delayed jobs."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]

    future_time = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    payload = {
        "project_slug": "doh-nut",
        "platform": "instagram",
        "action": "publish_post",
        "payload": {"caption": "Donut leleh karamel #DohNut"},
        "execute_at": future_time,
    }

    # 1. Schedule job (201 Created)
    create_resp = client.post("/api/social/schedule", json=payload, headers=headers, cookies=cookies)
    assert create_resp.status_code == 201, create_resp.text
    job_data = create_resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "pending"
    assert job_data["platform"] == "instagram"

    # 2. List scheduled jobs
    list_resp = client.get("/api/social/scheduled", headers=headers, cookies=cookies)
    assert list_resp.status_code == 200, list_resp.text
    jobs = list_resp.json()
    assert any(j["id"] == job_id for j in jobs)

    # 3. Cancel job
    cancel_resp = client.delete(f"/api/social/scheduled/{job_id}", headers=headers, cookies=cookies)
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["status"] == "cancelled"

    # 4. Cancel non-existent job returns 404
    fake_id = str(uuid.uuid4())
    fake_cancel = client.delete(f"/api/social/scheduled/{fake_id}", headers=headers, cookies=cookies)
    assert fake_cancel.status_code == 404


def test_generate_omnichannel_suite_has_validation():
    """Verify that generate-omnichannel returns validation metadata for all 4 platforms."""
    payload = {"topic": "AI Automation and Sovereign Workflows"}
    resp = client.post("/api/social/generate-omnichannel", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "draft_id" in data
    assert "validation" in data
    validation = data["validation"]
    for platform in ["facebook", "instagram", "tiktok", "youtube"]:
        assert platform in validation
        assert "valid" in validation[platform]
        assert "char_count" in validation[platform]


def test_action_omnichannel_draft_audit_log_and_history():
    """Verify that approving a draft stores reviewer_notes and writes an audit log entry retrievable via /history."""
    # 1. Create a draft first
    gen_resp = client.post("/api/social/generate-omnichannel", json={"topic": "Donut Glaze Special"})
    assert gen_resp.status_code == 200
    draft_id = gen_resp.json()["draft_id"]

    # 2. Action the draft with reviewer notes
    action_payload = {
        "draft_id": draft_id,
        "action": "approve",
        "reviewer_notes": "Approved for 4:30 PM tea time slot. Excellent hook.",
        "operator_id": "operator-megat"
    }
    act_resp = client.post("/api/social/omnichannel-action", json=action_payload)
    assert act_resp.status_code == 200, act_resp.text
    act_data = act_resp.json()
    assert act_data["status"] == "success"
    assert act_data["new_status"] == "approved"
    assert act_data["reviewer_notes"] == "Approved for 4:30 PM tea time slot. Excellent hook."
    assert act_data["approved_by"] == "operator-megat"
    assert "audit_id" in act_data

    # 3. Query audit history endpoint
    hist_resp = client.get(f"/api/social/omnichannel-drafts/{draft_id}/history")
    assert hist_resp.status_code == 200, hist_resp.text
    hist_data = hist_resp.json()
    assert hist_data["draft_id"] == draft_id
    assert len(hist_data["history"]) >= 1
    latest = hist_data["history"][0]
    assert latest["action"] == "approve"
    assert latest["reviewer_notes"] == "Approved for 4:30 PM tea time slot. Excellent hook."
    assert latest["operator_id"] == "operator-megat"


def test_generate_dohnut_social_suite_validation():
    """Verify that /api/dohnut/social/generate returns validation dictionary for 6 platforms."""
    payload = {"topic": "Kuih Burger Donut Special"}
    resp = client.post("/api/dohnut/social/generate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    assert "validation" in data
    val = data["validation"]
    for plat in ["tiktok", "instagram", "threads", "facebook", "x", "youtube"]:
        assert plat in val
        assert "valid" in val[plat]
        assert "char_count" in val[plat]

