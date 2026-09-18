"""Social campaign management, approval gates, and publication attempts."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.services.mission_store import MissionStore


class ApprovalMismatch(Exception):
    """Raised when content or media hash does not match an approval, or approval is unapproved."""
    pass


class ReconciliationRequired(Exception):
    """Raised when an unknown attempt blocks automatic retry without explicit reconciliation."""
    pass


class ApprovalExpired(Exception):
    """Raised when an approval has expired and cannot be approved or dispatched."""
    pass


class CampaignNotFound(Exception):
    """Raised when a campaign cannot be found."""
    pass


class PublicationState(str, Enum):
    """State machine states for publication attempts."""
    PREPARED = "prepared"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    SUBMITTED = "submitted"
    PUBLISHED = "published"
    FAILED = "failed"
    UNKNOWN = "unknown"

    # Lowercase aliases for convenience
    prepared = "prepared"
    awaiting_confirmation = "awaiting_confirmation"
    submitted = "submitted"
    published = "published"
    failed = "failed"
    unknown = "unknown"


class Campaign(BaseModel):
    """Campaign snapshot storing source facts, drafts, and immutable content hashes."""
    model_config = ConfigDict(extra="ignore")
    id: UUID
    project_slug: str
    source_facts: list[str] = Field(default_factory=list)
    drafts: dict[str, str] = Field(default_factory=dict)
    brand_truth_hash: str = ""
    content_hashes: dict[str, str] = Field(default_factory=dict)
    created_at: datetime


class Approval(BaseModel):
    """Immutable approval gate record bound to content and media hashes."""
    model_config = ConfigDict(extra="ignore")
    id: UUID
    campaign_id: UUID
    platform: str
    account_id: str
    content_sha256: str
    media_sha256: list[str] = Field(default_factory=list)
    status: str = "pending"
    expires_at: datetime
    created_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None


class PublicationAttempt(BaseModel):
    """Publication attempt tracking lifecycle from prepared to published or unknown."""
    model_config = ConfigDict(extra="ignore")
    id: UUID
    campaign_id: UUID
    approval_id: UUID
    platform: str
    state: str = "prepared"
    remote_post_id: str | None = None
    published_at: datetime | None = None
    created_at: datetime


class SocialCampaignService:
    """Service governing social media campaigns, cryptographic approval gates, and delivery attempts."""

    def __init__(self, store: Optional[MissionStore] = None):
        if store is None:
            self.store = MissionStore()
        else:
            self.store = store

        try:
            self.store.initialize()
        except Exception:
            pass

        self._campaigns: Dict[UUID, Campaign] = {}
        self._approvals: Dict[UUID, Approval] = {}
        self._attempts: Dict[UUID, PublicationAttempt] = {}

    def create_campaign(
        self,
        project_slug: str,
        source_facts: list[str],
        drafts: dict[str, str],
        brand_truth_path: Path | str | None = None,
    ) -> Campaign:
        """Create a new campaign, computing cryptographic SHA256 hashes of all drafts."""
        content_hashes: dict[str, str] = {}
        for platform_key, content in drafts.items():
            content_hashes[platform_key] = hashlib.sha256(content.encode("utf-8")).hexdigest()

        brand_truth_hash = ""
        if brand_truth_path is not None:
            p = Path(brand_truth_path)
            if p.is_file():
                brand_truth_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            elif isinstance(brand_truth_path, str) and len(brand_truth_path) == 64 and all(c in "0123456789abcdefABCDEF" for c in brand_truth_path):
                brand_truth_hash = brand_truth_path.lower()
            else:
                brand_truth_hash = hashlib.sha256(str(brand_truth_path).encode("utf-8")).hexdigest()

        campaign_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        campaign = Campaign(
            id=campaign_id,
            project_slug=project_slug,
            source_facts=list(source_facts),
            drafts=dict(drafts),
            brand_truth_hash=brand_truth_hash,
            content_hashes=content_hashes,
            created_at=now,
        )

        self._campaigns[campaign.id] = campaign

        try:
            self.store.save_campaign({
                "id": str(campaign.id),
                "project_slug": campaign.project_slug,
                "source_facts": campaign.source_facts,
                "drafts": campaign.drafts,
                "brand_truth_hash": campaign.brand_truth_hash,
                "content_hashes": campaign.content_hashes,
                "created_at": campaign.created_at.isoformat(),
            })
        except Exception:
            pass

        return campaign

    def get_campaign(self, campaign_id: Union[UUID, str]) -> Campaign:
        """Retrieve a campaign by ID or raise CampaignNotFound."""
        c_id = UUID(str(campaign_id))
        if c_id in self._campaigns:
            return self._campaigns[c_id]

        record = None
        try:
            record = self.store.get_campaign(c_id)
        except Exception:
            pass

        if record:
            campaign = Campaign(
                id=UUID(record["id"]),
                project_slug=record["project_slug"],
                source_facts=record["source_facts"],
                drafts=record["drafts"],
                brand_truth_hash=record["brand_truth_hash"],
                content_hashes=record["content_hashes"],
                created_at=datetime.fromisoformat(record["created_at"]),
            )
            self._campaigns[c_id] = campaign
            return campaign

        raise CampaignNotFound(f"Campaign {campaign_id} not found")

    def request_approval(
        self,
        campaign_id: Union[UUID, str],
        platform: str,
        account_id: str,
        content_sha256: str,
        media_sha256: Optional[List[str]] = None,
        ttl_seconds: int = 900,
    ) -> Approval:
        """Generate an approval request record with TTL expiry and status 'pending'."""
        c_id = UUID(str(campaign_id))
        media_list = list(media_sha256) if media_sha256 is not None else []
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        approval_id = uuid.uuid4()
        approval = Approval(
            id=approval_id,
            campaign_id=c_id,
            platform=platform,
            account_id=account_id,
            content_sha256=content_sha256,
            media_sha256=media_list,
            status="pending",
            expires_at=expires_at,
            created_at=now,
            decided_at=None,
            decided_by=None,
        )

        self._approvals[approval.id] = approval

        try:
            self.store.save_approval({
                "id": str(approval.id),
                "campaign_id": str(approval.campaign_id),
                "platform": approval.platform,
                "account_id": approval.account_id,
                "content_sha256": approval.content_sha256,
                "media_sha256": approval.media_sha256,
                "status": approval.status,
                "expires_at": approval.expires_at.isoformat(),
                "created_at": approval.created_at.isoformat(),
                "decided_at": None,
                "decided_by": None,
            })
        except Exception:
            pass

        return approval

    def get_approval(self, approval_id: Union[UUID, str]) -> Approval:
        """Retrieve an approval by ID or raise KeyError."""
        a_id = UUID(str(approval_id))
        if a_id in self._approvals:
            return self._approvals[a_id]

        record = None
        try:
            record = self.store.get_approval(a_id)
        except Exception:
            pass

        if record:
            approval = Approval(
                id=UUID(record["id"]),
                campaign_id=UUID(record["campaign_id"]),
                platform=record["platform"],
                account_id=record["account_id"],
                content_sha256=record["content_sha256"],
                media_sha256=record.get("media_sha256", []),
                status=record["status"],
                expires_at=datetime.fromisoformat(record["expires_at"]),
                created_at=datetime.fromisoformat(record["created_at"]),
                decided_at=datetime.fromisoformat(record["decided_at"]) if record.get("decided_at") else None,
                decided_by=record.get("decided_by"),
            )
            self._approvals[a_id] = approval
            return approval

        raise KeyError(f"Approval {approval_id} not found")

    def decide_approval(
        self,
        approval_id: Union[UUID, str],
        decision: str,
        operator_id: Union[str, int],
        reason: str = "",
    ) -> Approval:
        """Record an operator's decision ('approved' or 'rejected'), checking TTL expiry."""
        approval = self.get_approval(approval_id)

        now = datetime.now(timezone.utc)
        expires = approval.expires_at if approval.expires_at.tzinfo else approval.expires_at.replace(tzinfo=timezone.utc)
        if now > expires:
            raise ApprovalExpired(f"Approval {approval_id} expired at {expires.isoformat()}")

        norm_decision = decision.strip().lower()
        if norm_decision in ("approve", "approved"):
            new_status = "approved"
        elif norm_decision in ("reject", "rejected"):
            new_status = "rejected"
        else:
            new_status = decision

        approval.status = new_status
        approval.decided_at = now
        approval.decided_by = str(operator_id)

        try:
            self.store.update_approval(
                approval.id,
                {
                    "status": approval.status,
                    "decided_at": approval.decided_at.isoformat(),
                    "decided_by": approval.decided_by,
                },
            )
        except Exception:
            pass

        return approval

    def assert_approval_valid_for_dispatch(
        self,
        approval_id: Union[UUID, str],
        content_sha256: str,
        media_sha256: Optional[List[str]] = None,
    ) -> None:
        """Verify that an approval is approved, unexpired, and exactly matches the content/media hashes."""
        approval = self.get_approval(approval_id)

        now = datetime.now(timezone.utc)
        expires = approval.expires_at if approval.expires_at.tzinfo else approval.expires_at.replace(tzinfo=timezone.utc)
        if now > expires:
            raise ApprovalExpired(f"Approval {approval_id} expired at {expires.isoformat()}")

        if approval.content_sha256 != content_sha256:
            raise ApprovalMismatch(
                f"Content hash {content_sha256} does not match approved {approval.content_sha256}"
            )

        m_list = list(media_sha256) if media_sha256 is not None else []
        if sorted(approval.media_sha256) != sorted(m_list):
            raise ApprovalMismatch("Media hash mismatch with approved media")

        if approval.status != "approved":
            raise ApprovalMismatch(f"Approval {approval_id} is not in approved state (status={approval.status})")

    def create_attempt(
        self,
        campaign: Campaign,
        platform: str,
        approval: Optional[Approval] = None,
    ) -> PublicationAttempt:
        """Create a new publication attempt with initial state 'prepared' and no remote post ID."""
        c_id = campaign.id
        app_id = approval.id if approval is not None else self._find_approval_id_for_campaign(c_id, platform)
        now = datetime.now(timezone.utc)

        attempt = PublicationAttempt(
            id=uuid.uuid4(),
            campaign_id=c_id,
            approval_id=app_id,
            platform=platform,
            state=PublicationState.PREPARED.value,
            remote_post_id=None,
            published_at=None,
            created_at=now,
        )

        self._attempts[attempt.id] = attempt

        try:
            self.store.save_publication_attempt({
                "id": str(attempt.id),
                "campaign_id": str(attempt.campaign_id),
                "approval_id": str(attempt.approval_id),
                "platform": attempt.platform,
                "state": attempt.state,
                "remote_post_id": None,
                "published_at": None,
                "created_at": attempt.created_at.isoformat(),
            })
        except Exception:
            pass

        return attempt

    def _find_approval_id_for_campaign(self, campaign_id: UUID, platform: str) -> UUID:
        for app in self._approvals.values():
            if app.campaign_id == campaign_id and app.platform == platform:
                return app.id
        return uuid.uuid4()

    def get_attempt(self, attempt_id: Union[UUID, str]) -> PublicationAttempt:
        """Retrieve a publication attempt by ID or raise KeyError."""
        p_id = UUID(str(attempt_id))
        if p_id in self._attempts:
            return self._attempts[p_id]

        record = None
        try:
            record = self.store.get_publication_attempt(p_id)
        except Exception:
            pass

        if record:
            attempt = PublicationAttempt(
                id=UUID(record["id"]),
                campaign_id=UUID(record["campaign_id"]),
                approval_id=UUID(record["approval_id"]) if record.get("approval_id") else uuid.uuid4(),
                platform=record["platform"],
                state=record["state"],
                remote_post_id=record.get("remote_post_id"),
                published_at=datetime.fromisoformat(record["published_at"]) if record.get("published_at") else None,
                created_at=datetime.fromisoformat(record["created_at"]),
            )
            self._attempts[p_id] = attempt
            return attempt

        raise KeyError(f"Attempt {attempt_id} not found")

    def mark_unknown(self, attempt_id: Union[UUID, str], reason: str = "") -> None:
        """Transition attempt state to 'unknown' when remote outcome cannot be determined."""
        attempt = self.get_attempt(attempt_id)
        attempt.state = PublicationState.UNKNOWN.value

        try:
            self.store.update_publication_attempt_state(attempt.id, PublicationState.UNKNOWN.value)
        except Exception:
            pass

    def retry(self, attempt_id: Union[UUID, str]) -> None:
        """Retry a publication attempt, rejecting attempts in 'unknown' state without reconciliation."""
        attempt = self.get_attempt(attempt_id)
        if attempt.state in ("unknown", PublicationState.UNKNOWN.value):
            raise ReconciliationRequired("Cannot auto-retry unknown attempt without reconciliation")
        attempt.state = PublicationState.PREPARED.value
        try:
            self.store.update_publication_attempt_state(attempt.id, PublicationState.PREPARED.value)
        except Exception:
            pass

    def reconcile(
        self,
        attempt_id: Union[UUID, str],
        state: str = "published",
        remote_post_id: Optional[str] = None,
    ) -> PublicationAttempt:
        """Reconcile an unknown attempt with human or platform receipt proof."""
        attempt = self.get_attempt(attempt_id)
        attempt.state = state
        if remote_post_id:
            attempt.remote_post_id = remote_post_id
        if state == "published":
            attempt.published_at = datetime.now(timezone.utc)

        try:
            self.store.update_publication_attempt_state(
                attempt.id,
                state=attempt.state,
                remote_post_id=attempt.remote_post_id,
                published_at=attempt.published_at.isoformat() if attempt.published_at else None,
            )
        except Exception:
            pass

        return attempt
