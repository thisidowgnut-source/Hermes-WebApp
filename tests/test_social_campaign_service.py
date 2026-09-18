"""Unit tests for SocialCampaignService, cryptographic approval gates, and delivery state transitions."""
import hashlib
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend.services.mission_store import MissionStore
from backend.services.social_campaign_service import (
    Approval,
    ApprovalExpired,
    ApprovalMismatch,
    Campaign,
    CampaignNotFound,
    PublicationAttempt,
    PublicationState,
    ReconciliationRequired,
    SocialCampaignService,
)


@pytest.fixture
def store(tmp_path):
    """Provide an initialized MissionStore in a temporary database."""
    db_file = tmp_path / "test_social_campaign.db"
    s = MissionStore(db_file)
    s.initialize()
    return s


@pytest.fixture
def service(store):
    """Provide a SocialCampaignService backed by a test store."""
    return SocialCampaignService(store=store)


@pytest.fixture
def sample_drafts():
    return {
        "x": "Fresh donuts at Doh-Nut HQ today! Grab yours now. #GoodVibeGoodDoh",
        "instagram": "Glazed perfection in every bite. Tap link in bio for the flavor lineup! 🍩✨",
        "tiktok": "[Visual: Warm golden donut glazed in pink frosting] 'Try our new flavor today!'",
    }


@pytest.fixture
def campaign(service, sample_drafts):
    return service.create_campaign(
        project_slug="doh-nut",
        source_facts=["Store opens at 10 AM", "Free cold brew before noon"],
        drafts=sample_drafts,
    )


@pytest.fixture
def approved_campaign(service, campaign, sample_drafts):
    content_hash = hashlib.sha256(sample_drafts["instagram"].encode("utf-8")).hexdigest()
    approval = service.request_approval(
        campaign_id=campaign.id,
        platform="instagram",
        account_id="@thisisdohnut",
        content_sha256=content_hash,
        media_sha256=[],
        ttl_seconds=900,
    )
    service.decide_approval(approval.id, decision="approved", operator_id=12345)
    return campaign


def test_local_approval_does_not_mark_post_published(service, approved_campaign):
    """Local approval creates attempt with state='prepared', remote_post_id=None, published_at=None."""
    attempt = service.create_attempt(approved_campaign, platform="instagram")
    assert attempt.state == "prepared"
    assert attempt.state == PublicationState.PREPARED
    assert attempt.remote_post_id is None
    assert attempt.published_at is None
    assert attempt.campaign_id == approved_campaign.id


def test_content_change_invalidates_existing_approval(service, campaign):
    """Content change invalidates existing approval (raises ApprovalMismatch)."""
    hash_a = hashlib.sha256(b"Original content draft A").hexdigest()
    hash_b = hashlib.sha256(b"Tampered content draft B").hexdigest()

    approval = service.request_approval(
        campaign_id=campaign.id,
        platform="x",
        account_id="@thisisdohnut",
        content_sha256=hash_a,
        media_sha256=[],
    )

    # Even after approval, dispatching changed content must be rejected
    service.decide_approval(approval.id, decision="approved", operator_id=999)

    with pytest.raises(ApprovalMismatch):
        service.assert_approval_valid_for_dispatch(
            approval.id,
            content_sha256=hash_b,
            media_sha256=[],
        )


def test_expired_approval_cannot_be_approved_or_dispatched(service, campaign):
    """Expired approval cannot be approved or dispatched (raises ApprovalExpired)."""
    hash_content = hashlib.sha256(b"Some draft content").hexdigest()

    # Create an approval that is already expired (negative TTL)
    expired_approval = service.request_approval(
        campaign_id=campaign.id,
        platform="tiktok",
        account_id="@thisisdohnut",
        content_sha256=hash_content,
        media_sha256=[],
        ttl_seconds=-10,
    )

    # Attempting to approve an expired approval must raise ApprovalExpired
    with pytest.raises(ApprovalExpired):
        service.decide_approval(expired_approval.id, decision="approved", operator_id=101)

    # Attempting to dispatch with an expired approval must raise ApprovalExpired
    with pytest.raises(ApprovalExpired):
        service.assert_approval_valid_for_dispatch(
            expired_approval.id,
            content_sha256=hash_content,
            media_sha256=[],
        )


def test_unknown_dispatch_blocks_automatic_retry(service, campaign):
    """Unknown dispatch blocks automatic retry without reconciliation (raises ReconciliationRequired)."""
    attempt = service.create_attempt(campaign, platform="x")
    service.mark_unknown(attempt.id, reason="network_lost_after_submit")

    # Verify attempt state changed to unknown
    unknown_attempt = service.get_attempt(attempt.id)
    assert unknown_attempt.state == "unknown"

    with pytest.raises(ReconciliationRequired):
        service.retry(attempt.id)


def test_create_campaign_computes_sha256_hashes_for_drafts(service, sample_drafts):
    """create_campaign computes SHA256 hashes for all drafts."""
    campaign = service.create_campaign(
        project_slug="doh-nut",
        source_facts=["Brand system verified"],
        drafts=sample_drafts,
    )

    for platform_key, text in sample_drafts.items():
        expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert campaign.content_hashes[platform_key] == expected_hash

    assert len(campaign.content_hashes) == len(sample_drafts)
    assert campaign.project_slug == "doh-nut"


def test_brand_truth_hash_computation(service, tmp_path):
    """Brand truth hash should be calculated from file path, raw string, or empty when omitted."""
    # 1. From a file
    brand_file = tmp_path / "01-brand-truth.md"
    brand_file.write_text("# Doh-Nut Brand Truth\nSovereign sweetness.", encoding="utf-8")
    expected_file_hash = hashlib.sha256(brand_file.read_bytes()).hexdigest()

    camp_with_file = service.create_campaign(
        project_slug="doh-nut",
        source_facts=[],
        drafts={"x": "hello"},
        brand_truth_path=brand_file,
    )
    assert camp_with_file.brand_truth_hash == expected_file_hash

    # 2. When None
    camp_none = service.create_campaign(
        project_slug="doh-nut",
        source_facts=[],
        drafts={"x": "hello"},
        brand_truth_path=None,
    )
    assert camp_none.brand_truth_hash == ""


def test_media_hash_mismatch_raises_approval_mismatch(service, campaign):
    """Media hash changes must invalidate the approval."""
    content_hash = hashlib.sha256(b"Post text").hexdigest()
    media_a = hashlib.sha256(b"image1.jpg").hexdigest()
    media_b = hashlib.sha256(b"image2.jpg").hexdigest()

    approval = service.request_approval(
        campaign_id=campaign.id,
        platform="instagram",
        account_id="@thisisdohnut",
        content_sha256=content_hash,
        media_sha256=[media_a],
    )
    service.decide_approval(approval.id, "approved", operator_id=123)

    # Dispatched with media_b instead of media_a
    with pytest.raises(ApprovalMismatch):
        service.assert_approval_valid_for_dispatch(
            approval.id,
            content_sha256=content_hash,
            media_sha256=[media_b],
        )


def test_unapproved_status_blocks_dispatch(service, campaign):
    """Approval in pending or rejected status cannot be dispatched."""
    content_hash = hashlib.sha256(b"Post text").hexdigest()
    approval = service.request_approval(
        campaign_id=campaign.id,
        platform="x",
        account_id="@thisisdohnut",
        content_sha256=content_hash,
    )

    # Still pending
    with pytest.raises(ApprovalMismatch):
        service.assert_approval_valid_for_dispatch(approval.id, content_sha256=content_hash)

    # Rejected
    service.decide_approval(approval.id, "rejected", operator_id=555)
    with pytest.raises(ApprovalMismatch):
        service.assert_approval_valid_for_dispatch(approval.id, content_sha256=content_hash)


def test_reconciliation_allows_recovery_of_unknown_attempt(service, campaign):
    """Reconciling an unknown attempt transitions it to published and sets remote_post_id."""
    attempt = service.create_attempt(campaign, platform="facebook")
    service.mark_unknown(attempt.id, reason="timeout")

    reconciled = service.reconcile(attempt.id, state="published", remote_post_id="fb_post_98765")
    assert reconciled.state == "published"
    assert reconciled.remote_post_id == "fb_post_98765"
    assert reconciled.published_at is not None


def test_persistence_in_mission_store(store, sample_drafts):
    """Data persists across service instances backed by the same MissionStore."""
    service1 = SocialCampaignService(store=store)
    camp = service1.create_campaign(
        project_slug="doh-nut",
        source_facts=["Persistent fact"],
        drafts=sample_drafts,
    )
    c_hash = camp.content_hashes["x"]
    app = service1.request_approval(camp.id, "x", "@thisisdohnut", c_hash)
    service1.decide_approval(app.id, "approved", operator_id=42)
    att = service1.create_attempt(camp, "x", app)

    # New service instance sharing same store
    service2 = SocialCampaignService(store=store)
    recovered_camp = service2.get_campaign(camp.id)
    assert recovered_camp.project_slug == "doh-nut"
    assert recovered_camp.content_hashes["x"] == c_hash

    recovered_app = service2.get_approval(app.id)
    assert recovered_app.status == "approved"
    assert recovered_app.decided_by == "42"

    recovered_att = service2.get_attempt(att.id)
    assert recovered_att.state == "prepared"
    assert recovered_att.campaign_id == camp.id


def test_get_nonexistent_campaign_raises_campaign_not_found(service):
    """Querying a non-existent campaign raises CampaignNotFound."""
    with pytest.raises(CampaignNotFound):
        service.get_campaign(uuid.uuid4())
