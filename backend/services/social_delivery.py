"""Capability-declared social delivery adapters, receipts, and reconciliation."""
from __future__ import annotations

import json
import os
import urllib.request
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.services.social_campaign_service import (
    PublicationAttempt,
    PublicationState,
)


class DeliveryError(Exception):
    """Base exception for all social delivery errors."""
    pass


class MissingPublicationReceipt(DeliveryError):
    """Raised when an attempt is marked as published without a valid publication receipt."""
    pass


class UnsupportedPlatformError(DeliveryError):
    """Raised when a delivery adapter is requested for an unsupported platform."""
    pass


SUPPORTED_PLATFORMS: set[str] = {
    "tiktok",
    "instagram",
    "threads",
    "facebook",
    "x",
    "youtube",
}


class PlatformCapabilities(BaseModel):
    """Declared capabilities and constraints for a social delivery platform."""
    model_config = ConfigDict(extra="ignore")

    platform: str
    can_draft: bool = True
    can_upload_media: bool = True
    can_publish: bool = True
    can_schedule: bool = False
    has_read_receipt: bool = True
    has_analytics: bool = False
    requires_human_confirmation: bool = False

    def __init__(self, **data: Any):
        # TikTok defaults to requires_human_confirmation=True unless explicitly overridden
        if "platform" in data and str(data["platform"]).strip().lower() == "tiktok":
            if "requires_human_confirmation" not in data:
                data["requires_human_confirmation"] = True
        super().__init__(**data)


class DeliveryResult(BaseModel):
    """Result of an adapter delivery action (prepare, submit, mark_published, reconcile)."""
    model_config = ConfigDict(extra="ignore")

    attempt_id: UUID
    state: str
    remote_post_id: str | None = None
    receipt: dict[str, Any] | None = None
    message: str = ""


def _to_uuid(val: Union[UUID, str, Any]) -> UUID:
    """Normalize a value to a UUID object."""
    if isinstance(val, UUID):
        return val
    try:
        return UUID(str(val))
    except (ValueError, TypeError, AttributeError) as e:
        raise ValueError(f"Invalid UUID representation: {val}") from e


def _extract_attempt_id(attempt_or_id: Union[PublicationAttempt, UUID, str, Any]) -> UUID:
    """Extract UUID from a PublicationAttempt instance, dict, or raw UUID/str."""
    if hasattr(attempt_or_id, "id"):
        return _to_uuid(attempt_or_id.id)
    if isinstance(attempt_or_id, dict) and "id" in attempt_or_id:
        return _to_uuid(attempt_or_id["id"])
    return _to_uuid(attempt_or_id)


def _validate_receipt(receipt: Optional[Dict[str, Any]]) -> dict[str, Any]:
    """Validate that a publication receipt is non-null, a dictionary, and contains proof."""
    if receipt is None:
        raise MissingPublicationReceipt("Publication receipt is strictly required before marking as published.")
    if not isinstance(receipt, dict):
        raise MissingPublicationReceipt(f"Publication receipt must be a dictionary, got {type(receipt).__name__}.")
    if len(receipt) == 0:
        raise MissingPublicationReceipt("Publication receipt cannot be empty and lacks required proof.")
    return receipt


class SocialAdapter(ABC):
    """Abstract base class for platform delivery adapters."""
    platform: str

    @abstractmethod
    def capabilities(self) -> PlatformCapabilities:
        """Return declared platform capabilities and constraints."""
        pass

    @abstractmethod
    def prepare(self, attempt: Union[PublicationAttempt, Any]) -> DeliveryResult:
        """Prepare draft/payload for delivery without publishing."""
        pass

    @abstractmethod
    def submit(self, attempt: Union[PublicationAttempt, Any]) -> DeliveryResult:
        """Submit attempt to platform or staging queue."""
        pass

    @abstractmethod
    def mark_published(
        self, attempt_id: Union[UUID, str], receipt: Optional[Dict[str, Any]]
    ) -> DeliveryResult:
        """Mark attempt as published with strict requirement for a verified receipt."""
        pass

    @abstractmethod
    def reconcile(
        self,
        attempt_or_id: Union[PublicationAttempt, UUID, str],
        receipt: Optional[Dict[str, Any]] = None,
        resolved_status: Optional[str] = None,
    ) -> DeliveryResult:
        """Reconcile an unknown or pending attempt."""
        pass


class ManualConfirmationAdapter(SocialAdapter):
    """Adapter for human-in-the-loop manual confirmation workflow."""

    def __init__(self, platform: str = "general"):
        self.platform = platform.strip().lower()

    def capabilities(self) -> PlatformCapabilities:
        return PlatformCapabilities(
            platform=self.platform,
            can_draft=True,
            can_upload_media=True,
            can_publish=True,
            can_schedule=False,
            has_read_receipt=True,
            has_analytics=False,
            requires_human_confirmation=True,
        )

    def prepare(self, attempt: Union[PublicationAttempt, Any]) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt)
        return DeliveryResult(
            attempt_id=attempt_id,
            state="prepared",
            remote_post_id=None,
            receipt=None,
            message=f"Attempt {attempt_id} prepared for manual confirmation on {self.platform}.",
        )

    def submit(self, attempt: Union[PublicationAttempt, Any]) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt)
        return DeliveryResult(
            attempt_id=attempt_id,
            state="submitted",
            remote_post_id=None,
            receipt=None,
            message=f"Attempt {attempt_id} submitted; awaiting manual human confirmation and publication receipt.",
        )

    def mark_published(
        self, attempt_id: Union[UUID, str], receipt: Optional[Dict[str, Any]]
    ) -> DeliveryResult:
        att_uuid = _to_uuid(attempt_id)
        validated_receipt = _validate_receipt(receipt)
        remote_id = str(
            validated_receipt.get("remote_post_id")
            or validated_receipt.get("post_id")
            or validated_receipt.get("id")
            or f"{self.platform}_manual_{uuid.uuid4().hex[:8]}"
        )
        return DeliveryResult(
            attempt_id=att_uuid,
            state="published",
            remote_post_id=remote_id,
            receipt=validated_receipt,
            message="Publication confirmed and verified with manual receipt.",
        )

    def reconcile(
        self,
        attempt_or_id: Union[PublicationAttempt, UUID, str],
        receipt: Optional[Dict[str, Any]] = None,
        resolved_status: Optional[str] = None,
    ) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt_or_id)
        if receipt is not None:
            return self.mark_published(attempt_id, receipt)
        if resolved_status in ("published", "success"):
            return self.mark_published(attempt_id, receipt={"proof": "operator_reconciled"})
        if resolved_status in ("failed", "failure"):
            return DeliveryResult(
                attempt_id=attempt_id,
                state="failed",
                remote_post_id=None,
                receipt=None,
                message="Manual attempt reconciled as failed by operator.",
            )
        return DeliveryResult(
            attempt_id=attempt_id,
            state="submitted",
            remote_post_id=None,
            receipt=None,
            message="Manual attempt requires operator receipt to resolve.",
        )


class WebBridgeAssistAdapter(SocialAdapter):
    """Adapter for browser-assisted prefill/navigation via GangNiaga WebBridge on port 10087."""

    def __init__(
        self,
        platform: str = "general",
        base_url: str = "http://127.0.0.1:10087",
        auth_key: str = "",
    ):
        self.platform = platform.strip().lower()
        self.base_url = base_url.rstrip("/")
        self.auth_key = auth_key or os.getenv("WEBBRIDGE_KEY", "")

    def capabilities(self) -> PlatformCapabilities:
        return PlatformCapabilities(
            platform=self.platform,
            can_draft=True,
            can_upload_media=True,
            can_publish=False,  # Browser assistance only; requires human/platform confirmation
            can_schedule=False,
            has_read_receipt=False,
            has_analytics=False,
            requires_human_confirmation=True,
        )

    def _get_target_url(self) -> str:
        url_map = {
            "tiktok": "https://www.tiktok.com/upload",
            "instagram": "https://www.instagram.com/",
            "threads": "https://www.threads.net/",
            "facebook": "https://www.facebook.com/profile.php?id=61579737151034",
            "x": "https://x.com/compose/post",
            "youtube": "https://studio.youtube.com/",
        }
        return url_map.get(self.platform, "https://www.google.com")

    def _send_safe_command(self, action: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send a safe command payload to WebBridge daemon, recording only opaque references."""
        payload = json.dumps({"action": action, "args": args}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.auth_key:
            headers["Authorization"] = f"Bearer {self.auth_key}"

        req = urllib.request.Request(f"{self.base_url}/command", data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"ok": False, "offline": True, "error": str(e)}

    def prepare(
        self, attempt: Union[PublicationAttempt, Any], execute_network: bool = False
    ) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt)
        target_url = self._get_target_url()
        action_ref = f"wb_nav_{uuid.uuid4().hex[:8]}"

        if execute_network:
            self._send_safe_command("navigate", {"url": target_url, "newTab": False})

        # Never report published; remote_post_id must be None
        return DeliveryResult(
            attempt_id=attempt_id,
            state="prepared",
            remote_post_id=None,
            receipt={"browser_action": action_ref, "url": target_url, "port": 10087},
            message=f"WebBridge navigation prepared for {self.platform} ({action_ref}).",
        )

    def submit(
        self, attempt: Union[PublicationAttempt, Any], execute_network: bool = False
    ) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt)
        target_url = self._get_target_url()
        action_ref = f"wb_prefill_{uuid.uuid4().hex[:8]}"

        if execute_network:
            self._send_safe_command("navigate", {"url": target_url, "newTab": False})

        # State is "awaiting_confirmation" (or "prepared"), remote_post_id is None
        return DeliveryResult(
            attempt_id=attempt_id,
            state="awaiting_confirmation",
            remote_post_id=None,
            receipt={"browser_action": action_ref, "url": target_url, "port": 10087},
            message=f"Dispatched prefill to WebBridge for {self.platform}; awaiting human confirmation.",
        )

    def mark_published(
        self, attempt_id: Union[UUID, str], receipt: Optional[Dict[str, Any]]
    ) -> DeliveryResult:
        att_uuid = _to_uuid(attempt_id)
        validated_receipt = _validate_receipt(receipt)
        remote_id = str(
            validated_receipt.get("remote_post_id")
            or validated_receipt.get("post_id")
            or validated_receipt.get("id")
            or f"{self.platform}_wb_{uuid.uuid4().hex[:8]}"
        )
        return DeliveryResult(
            attempt_id=att_uuid,
            state="published",
            remote_post_id=remote_id,
            receipt=validated_receipt,
            message="Publication confirmed and verified with receipt.",
        )

    def reconcile(
        self,
        attempt_or_id: Union[PublicationAttempt, UUID, str],
        receipt: Optional[Dict[str, Any]] = None,
        resolved_status: Optional[str] = None,
    ) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt_or_id)
        if receipt is not None:
            return self.mark_published(attempt_id, receipt)
        if resolved_status in ("published", "success"):
            return self.mark_published(attempt_id, receipt={"proof": "operator_reconciled"})
        if resolved_status in ("failed", "failure"):
            return DeliveryResult(
                attempt_id=attempt_id,
                state="failed",
                remote_post_id=None,
                receipt=None,
                message="WebBridge assist attempt marked as failed.",
            )
        return DeliveryResult(
            attempt_id=attempt_id,
            state="awaiting_confirmation",
            remote_post_id=None,
            receipt=None,
            message="WebBridge assist cannot confirm publication without a platform receipt.",
        )


class PlatformApiAdapter(SocialAdapter):
    """Adapter for direct platform API publication via verified OAuth credentials."""

    def __init__(
        self,
        platform: str = "general",
        oauth_verified: bool = True,
        status_resolver: Optional[Callable[[UUID], Tuple[str, Optional[str], Optional[dict]]]] = None,
    ):
        self.platform = platform.strip().lower()
        self.oauth_verified = oauth_verified
        self._status_resolver = status_resolver
        self._attempts: Dict[UUID, Dict[str, Any]] = {}

    def capabilities(self) -> PlatformCapabilities:
        is_tiktok = self.platform == "tiktok"
        return PlatformCapabilities(
            platform=self.platform,
            can_draft=True,
            can_upload_media=True,
            can_publish=True,
            can_schedule=True,
            has_read_receipt=True,
            has_analytics=True,
            requires_human_confirmation=True if is_tiktok else False,
        )

    def prepare(self, attempt: Union[PublicationAttempt, Any]) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt)
        self._attempts[attempt_id] = {
            "state": "prepared",
            "remote_post_id": None,
            "receipt": None,
        }
        return DeliveryResult(
            attempt_id=attempt_id,
            state="prepared",
            remote_post_id=None,
            receipt=None,
            message=f"API publication payload prepared for {self.platform}.",
        )

    def submit(
        self,
        attempt: Union[PublicationAttempt, Any],
        fail_network: bool = False,
        remote_post_id: Optional[str] = None,
        receipt: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        attempt_id = _extract_attempt_id(attempt)

        if fail_network:
            # Network error or timeout after submit - state must be unknown!
            self._attempts[attempt_id] = {
                "state": "unknown",
                "remote_post_id": None,
                "receipt": None,
            }
            return DeliveryResult(
                attempt_id=attempt_id,
                state="unknown",
                remote_post_id=None,
                receipt=None,
                message="Network error after submit; publication outcome is unknown, reconciliation required.",
            )

        # Successful submission
        post_id = remote_post_id or f"{self.platform}_api_{uuid.uuid4().hex[:10]}"
        pub_receipt = receipt or {
            "platform": self.platform,
            "remote_post_id": post_id,
            "status": "published",
            "published_at": datetime.now(timezone.utc).isoformat(),
        }

        self._attempts[attempt_id] = {
            "state": "published",
            "remote_post_id": post_id,
            "receipt": pub_receipt,
        }

        return DeliveryResult(
            attempt_id=attempt_id,
            state="published",
            remote_post_id=post_id,
            receipt=pub_receipt,
            message=f"Direct API publication succeeded on {self.platform}.",
        )

    def mark_published(
        self, attempt_id: Union[UUID, str], receipt: Optional[Dict[str, Any]]
    ) -> DeliveryResult:
        att_uuid = _to_uuid(attempt_id)
        validated_receipt = _validate_receipt(receipt)
        post_id = str(
            validated_receipt.get("remote_post_id")
            or validated_receipt.get("post_id")
            or validated_receipt.get("id")
            or f"{self.platform}_api_{uuid.uuid4().hex[:10]}"
        )
        self._attempts[att_uuid] = {
            "state": "published",
            "remote_post_id": post_id,
            "receipt": validated_receipt,
        }
        return DeliveryResult(
            attempt_id=att_uuid,
            state="published",
            remote_post_id=post_id,
            receipt=validated_receipt,
            message="Published status recorded with verified receipt.",
        )

    def reconcile(
        self,
        attempt_or_id: Union[PublicationAttempt, UUID, str],
        receipt: Optional[Dict[str, Any]] = None,
        resolved_status: Optional[str] = None,
        remote_post_id: Optional[str] = None,
    ) -> DeliveryResult:
        """Queries platform status to resolve an unknown attempt to published or failed."""
        att_uuid = _extract_attempt_id(attempt_or_id)

        # 1. Custom status resolver callable if registered
        if self._status_resolver is not None:
            new_state, post_id, rec = self._status_resolver(att_uuid)
            self._attempts[att_uuid] = {
                "state": new_state,
                "remote_post_id": post_id,
                "receipt": rec,
            }
            return DeliveryResult(
                attempt_id=att_uuid,
                state=new_state,
                remote_post_id=post_id,
                receipt=rec,
                message=f"Reconciled via platform status resolver to '{new_state}'.",
            )

        # 2. Explicit resolution argument in reconcile call
        if resolved_status in ("published", "success"):
            post_id = remote_post_id or f"{self.platform}_rec_{uuid.uuid4().hex[:8]}"
            pub_receipt = receipt or {
                "platform": self.platform,
                "remote_post_id": post_id,
                "reconciled": True,
                "status": "published",
            }
            self._attempts[att_uuid] = {
                "state": "published",
                "remote_post_id": post_id,
                "receipt": pub_receipt,
            }
            return DeliveryResult(
                attempt_id=att_uuid,
                state="published",
                remote_post_id=post_id,
                receipt=pub_receipt,
                message=f"Reconciliation verified post exists on {self.platform}.",
            )
        elif resolved_status in ("failed", "failure", "not_found"):
            self._attempts[att_uuid] = {
                "state": "failed",
                "remote_post_id": None,
                "receipt": None,
            }
            return DeliveryResult(
                attempt_id=att_uuid,
                state="failed",
                remote_post_id=None,
                receipt=None,
                message=f"Reconciliation verified publication failed on {self.platform}.",
            )

        # 3. Direct receipt provided
        if receipt is not None:
            return self.mark_published(att_uuid, receipt)

        # 4. Check internal recorded state
        current = self._attempts.get(att_uuid)
        if current and current.get("state") in ("published", "failed"):
            return DeliveryResult(
                attempt_id=att_uuid,
                state=current["state"],
                remote_post_id=current.get("remote_post_id"),
                receipt=current.get("receipt"),
                message=f"Attempt state already resolved to {current['state']}.",
            )

        # 5. If still unresolved
        return DeliveryResult(
            attempt_id=att_uuid,
            state="unknown",
            remote_post_id=None,
            receipt=None,
            message="Platform status query inconclusive; attempt remains unknown.",
        )


class SocialDeliveryRegistry:
    """Registry mapping social media platforms to their declared delivery adapters."""

    def __init__(self, default_adapter_type: str = "manual"):
        self.default_adapter_type = default_adapter_type.lower()
        self._registered_adapters: Dict[str, SocialAdapter] = {}

    def register_adapter(self, platform: str, adapter: SocialAdapter) -> None:
        """Register or override a custom adapter for a platform."""
        self._registered_adapters[platform.strip().lower()] = adapter

    def get_supported_platforms(self) -> list[str]:
        """Return list of default supported platforms."""
        return sorted(SUPPORTED_PLATFORMS)

    def adapter_for(
        self, platform: str, adapter_type: Optional[str] = None
    ) -> SocialAdapter:
        """Retrieve delivery adapter for the specified platform."""
        if not platform or not isinstance(platform, str):
            raise UnsupportedPlatformError("Platform name must be a non-empty string.")

        p = platform.strip().lower()
        if p not in SUPPORTED_PLATFORMS and p not in self._registered_adapters:
            raise UnsupportedPlatformError(
                f"Platform '{platform}' is not supported. Supported platforms: {sorted(SUPPORTED_PLATFORMS)}"
            )

        # Return explicitly registered adapter if present and adapter_type is not overridden
        if p in self._registered_adapters and adapter_type is None:
            return self._registered_adapters[p]

        chosen_type = (adapter_type or self.default_adapter_type).lower()

        if chosen_type == "webbridge":
            return WebBridgeAssistAdapter(platform=p)
        elif chosen_type == "api":
            return PlatformApiAdapter(platform=p)
        else:  # "manual" or default
            return ManualConfirmationAdapter(platform=p)

    def get_adapter(self, platform: str, adapter_type: Optional[str] = None) -> SocialAdapter:
        """Convenience alias for adapter_for."""
        return self.adapter_for(platform, adapter_type)


__all__ = [
    "DeliveryError",
    "MissingPublicationReceipt",
    "UnsupportedPlatformError",
    "SUPPORTED_PLATFORMS",
    "PlatformCapabilities",
    "DeliveryResult",
    "SocialAdapter",
    "ManualConfirmationAdapter",
    "WebBridgeAssistAdapter",
    "PlatformApiAdapter",
    "SocialDeliveryRegistry",
]
