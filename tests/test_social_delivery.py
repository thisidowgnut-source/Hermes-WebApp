"""Unit tests for capability-declared social delivery adapters, receipts, and reconciliation."""
import uuid
from datetime import datetime, timezone

import pytest

from backend.services.social_campaign_service import (
    PublicationAttempt,
    PublicationState,
)
from backend.services.social_delivery import (
    DeliveryError,
    DeliveryResult,
    ManualConfirmationAdapter,
    MissingPublicationReceipt,
    PlatformApiAdapter,
    PlatformCapabilities,
    SocialAdapter,
    SocialDeliveryRegistry,
    SUPPORTED_PLATFORMS,
    UnsupportedPlatformError,
    WebBridgeAssistAdapter,
)


@pytest.fixture
def approved_attempt():
    """Provide a sample approved PublicationAttempt."""
    return PublicationAttempt(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        approval_id=uuid.uuid4(),
        platform="instagram",
        state="prepared",
        remote_post_id=None,
        published_at=None,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def manual_adapter():
    """Provide a ManualConfirmationAdapter for Instagram."""
    return ManualConfirmationAdapter(platform="instagram")


@pytest.fixture
def webbridge_adapter():
    """Provide a WebBridgeAssistAdapter for Instagram."""
    return WebBridgeAssistAdapter(platform="instagram")


@pytest.fixture
def registry():
    """Provide a fresh SocialDeliveryRegistry."""
    return SocialDeliveryRegistry()


# --- Requirement 1: WebBridge Navigation is prepared/awaiting_confirmation, never published without receipt ---

def test_webbridge_navigation_is_prepared_not_published(webbridge_adapter, approved_attempt):
    """WebBridge navigation results in 'prepared' or 'awaiting_confirmation', never published."""
    # 1. Prepare stage
    result_prep = webbridge_adapter.prepare(approved_attempt)
    assert result_prep.state in ("prepared", "awaiting_confirmation")
    assert result_prep.state == "prepared"
    assert result_prep.remote_post_id is None
    assert result_prep.attempt_id == approved_attempt.id
    assert "browser_action" in result_prep.receipt
    assert result_prep.receipt.get("port") == 10087

    # 2. Submit stage (prefill dispatched)
    result_submit = webbridge_adapter.submit(approved_attempt)
    assert result_submit.state in ("prepared", "awaiting_confirmation")
    assert result_submit.state == "awaiting_confirmation"
    assert result_submit.remote_post_id is None
    assert result_submit.attempt_id == approved_attempt.id
    assert "browser_action" in result_submit.receipt


def test_webbridge_capabilities_require_human_confirmation(webbridge_adapter):
    """WebBridgeAssistAdapter capabilities always require human confirmation."""
    caps = webbridge_adapter.capabilities()
    assert caps.can_draft is True
    assert caps.can_upload_media is True
    assert caps.can_publish is False  # Cannot publish directly without operator/receipt
    assert caps.requires_human_confirmation is True


# --- Requirement 2: Receipt is strictly required before marking published ---

def test_receipt_is_required_before_published(manual_adapter, approved_attempt):
    """Receipt is strictly required before marking published; None or empty raises MissingPublicationReceipt."""
    # Submit returns state="submitted"
    submit_result = manual_adapter.submit(approved_attempt)
    assert submit_result.state == "submitted"
    assert submit_result.remote_post_id is None

    # 1. None receipt must raise MissingPublicationReceipt
    with pytest.raises(MissingPublicationReceipt):
        manual_adapter.mark_published(approved_attempt.id, receipt=None)

    # 2. Empty receipt dict must raise MissingPublicationReceipt
    with pytest.raises(MissingPublicationReceipt):
        manual_adapter.mark_published(approved_attempt.id, receipt={})

    # 3. Non-dict receipt must raise MissingPublicationReceipt
    with pytest.raises(MissingPublicationReceipt):
        manual_adapter.mark_published(approved_attempt.id, receipt="invalid_receipt_string")  # type: ignore

    # 4. Valid receipt successfully marks as published
    valid_receipt = {
        "remote_post_id": "ig_live_post_555",
        "url": "https://www.instagram.com/p/live555",
        "confirmed_by": "operator_42",
    }
    published_result = manual_adapter.mark_published(approved_attempt.id, receipt=valid_receipt)
    assert published_result.state == "published"
    assert published_result.remote_post_id == "ig_live_post_555"
    assert published_result.receipt == valid_receipt
    assert published_result.attempt_id == approved_attempt.id


def test_webbridge_mark_published_requires_receipt(webbridge_adapter, approved_attempt):
    """WebBridgeAssistAdapter also enforces strict receipt validation before publishing."""
    with pytest.raises(MissingPublicationReceipt):
        webbridge_adapter.mark_published(approved_attempt.id, receipt=None)

    valid_receipt = {"post_id": "ig_wb_888", "proof": "screenshot_verified"}
    pub = webbridge_adapter.mark_published(approved_attempt.id, receipt=valid_receipt)
    assert pub.state == "published"
    assert pub.remote_post_id == "ig_wb_888"


# --- Requirement 3: TikTok capabilities default to requires_human_confirmation is True ---

def test_tiktok_defaults_to_human_confirmation(registry):
    """TikTok adapter capabilities must default to requires_human_confirmation=True."""
    tiktok_adapter = registry.adapter_for("tiktok")
    caps = tiktok_adapter.capabilities()
    assert caps.requires_human_confirmation is True
    assert caps.platform == "tiktok"

    # Also verify across other adapter types for TikTok
    wb_tiktok = registry.adapter_for("tiktok", adapter_type="webbridge")
    assert wb_tiktok.capabilities().requires_human_confirmation is True

    api_tiktok = registry.adapter_for("tiktok", adapter_type="api")
    assert api_tiktok.capabilities().requires_human_confirmation is True


def test_platform_capabilities_tiktok_default():
    """PlatformCapabilities model automatically defaults TikTok to requires_human_confirmation=True."""
    caps = PlatformCapabilities(platform="tiktok")
    assert caps.requires_human_confirmation is True

    caps_upper = PlatformCapabilities(platform="TIKTOK")
    assert caps_upper.requires_human_confirmation is True

    # Other platforms default to False unless set otherwise
    x_caps = PlatformCapabilities(platform="x")
    assert x_caps.requires_human_confirmation is False


# --- Requirement 4: Unknown attempt reconciliation ---

def test_unknown_attempt_reconciliation(approved_attempt):
    """PlatformApiAdapter transitions to 'unknown' on network loss, and resolves via reconcile."""
    api_adapter = PlatformApiAdapter(platform="x")

    # 1. Simulate network failure after submit -> state becomes "unknown"
    submit_res = api_adapter.submit(approved_attempt, fail_network=True)
    assert submit_res.state == "unknown"
    assert submit_res.remote_post_id is None
    assert submit_res.receipt is None

    # 2. Reconcile to published
    rec_pub = api_adapter.reconcile(
        approved_attempt.id,
        resolved_status="published",
        remote_post_id="x_post_99999",
        receipt={"post_id": "x_post_99999", "status": "active"},
    )
    assert rec_pub.state == "published"
    assert rec_pub.remote_post_id == "x_post_99999"
    assert rec_pub.receipt is not None
    assert rec_pub.attempt_id == approved_attempt.id

    # 3. Another attempt failing and reconciled to failed
    fail_attempt = PublicationAttempt(
        id=uuid.uuid4(),
        campaign_id=approved_attempt.campaign_id,
        approval_id=approved_attempt.approval_id,
        platform="x",
        state="prepared",
        created_at=datetime.now(timezone.utc),
    )
    api_adapter.submit(fail_attempt, fail_network=True)

    rec_fail = api_adapter.reconcile(fail_attempt.id, resolved_status="failed")
    assert rec_fail.state == "failed"
    assert rec_fail.remote_post_id is None
    assert rec_fail.attempt_id == fail_attempt.id


def test_platform_api_adapter_status_resolver(approved_attempt):
    """PlatformApiAdapter supports custom status_resolver callable during reconciliation."""
    def custom_resolver(attempt_id: uuid.UUID):
        return ("published", "resolved_id_123", {"source": "custom_resolver"})

    adapter = PlatformApiAdapter(platform="threads", status_resolver=custom_resolver)
    adapter.submit(approved_attempt, fail_network=True)

    result = adapter.reconcile(approved_attempt.id)
    assert result.state == "published"
    assert result.remote_post_id == "resolved_id_123"
    assert result.receipt == {"source": "custom_resolver"}


# --- Requirement 5: Unsupported platform raises UnsupportedPlatformError ---

def test_unsupported_platform_raises_unsupported_platform_error(registry):
    """Unsupported platforms raise UnsupportedPlatformError."""
    with pytest.raises(UnsupportedPlatformError, match="not supported"):
        registry.adapter_for("myspace")

    with pytest.raises(UnsupportedPlatformError):
        registry.adapter_for("friendster")

    with pytest.raises(UnsupportedPlatformError):
        registry.adapter_for("unknown_social_network")

    with pytest.raises(UnsupportedPlatformError):
        registry.adapter_for("")


# --- Additional platform coverage and edge cases ---

def test_all_default_supported_platforms(registry):
    """All standard default platforms are supported and return valid adapters."""
    expected = {"tiktok", "instagram", "threads", "facebook", "x", "youtube"}
    assert set(registry.get_supported_platforms()) == expected

    for p in expected:
        adapter = registry.adapter_for(p)
        assert isinstance(adapter, SocialAdapter)
        assert adapter.capabilities().platform == p


def test_case_insensitive_platform_lookup(registry):
    """Platform lookup is case-insensitive."""
    assert registry.adapter_for("TikTok").capabilities().platform == "tiktok"
    assert registry.adapter_for("INSTAGRAM").capabilities().platform == "instagram"
    assert registry.adapter_for("Threads").capabilities().platform == "threads"
    assert registry.adapter_for("X").capabilities().platform == "x"
    assert registry.adapter_for("YouTube").capabilities().platform == "youtube"


def test_custom_adapter_registration(registry, approved_attempt):
    """Custom adapter can be registered and retrieved from registry."""
    class CustomPlatformAdapter(SocialAdapter):
        platform = "bluesky"

        def capabilities(self):
            return PlatformCapabilities(platform="bluesky", can_publish=True)

        def prepare(self, attempt):
            return DeliveryResult(attempt_id=attempt.id, state="prepared")

        def submit(self, attempt):
            return DeliveryResult(attempt_id=attempt.id, state="submitted")

        def mark_published(self, attempt_id, receipt):
            if not receipt:
                raise MissingPublicationReceipt("Missing receipt")
            return DeliveryResult(attempt_id=attempt_id, state="published", receipt=receipt)

        def reconcile(self, attempt_or_id, receipt=None, resolved_status=None):
            return DeliveryResult(attempt_id=approved_attempt.id, state="reconciled")

    custom = CustomPlatformAdapter()
    registry.register_adapter("bluesky", custom)

    resolved = registry.adapter_for("bluesky")
    assert resolved == custom
    assert resolved.capabilities().platform == "bluesky"


def test_exception_inheritance():
    """All custom exceptions properly inherit from DeliveryError and Exception."""
    assert issubclass(MissingPublicationReceipt, DeliveryError)
    assert issubclass(UnsupportedPlatformError, DeliveryError)
    assert issubclass(DeliveryError, Exception)
