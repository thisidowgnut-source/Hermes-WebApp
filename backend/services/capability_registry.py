"""Capability registry enforcing least-privilege capability selection and bounded tool containment."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from backend.models.mission import CapabilityReceipt, PrimaryExecutor
from backend.services.orchestration_policy import (
    OrchestrationPolicy,
    UnknownCapability,
)


class CapabilityRegistry:
    """Registry that maps declared mission intent to fixed, verified capability profiles."""

    DEFAULT_POLICY_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / "config"
        / "orchestration"
        / "defaults.json"
    )

    FORBIDDEN_TOOL_TOKENS = (
        "shell",
        "bash",
        "exec",
        "terminal",
        "eval",
        "subprocess",
        "raw_command",
        "browser_publish",
        "credential_write",
        "financial_action",
        "external_transmission",
    )

    def __init__(self, config_path: Path | str | None = None) -> None:
        self.config_path = Path(config_path) if config_path else self.DEFAULT_POLICY_PATH
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Capability registry configuration not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as err:
            raise ValueError(f"Failed to load registry defaults: {err}") from err

        self.registry_version: str = data.get("policy_version", "1.0.0")
        self.capabilities: dict[str, Any] = data.get("capabilities", {})
        self.risk_classes: dict[str, list[str]] = data.get("risk_classes", {})

    def resolve_requested_capability(self, cap_name: str) -> dict[str, Any]:
        """Resolves capability definition by key or profile id.

        Raises UnknownCapability if not declared in defaults.
        """
        # Direct key match
        if cap_name in self.capabilities:
            return self.capabilities[cap_name]

        # Profile ID match (e.g. cap-plan)
        for cap_data in self.capabilities.values():
            if isinstance(cap_data, dict) and cap_data.get("id") == cap_name:
                return cap_data

        raise UnknownCapability(
            f"Capability '{cap_name}' is not registered in orchestration defaults."
        )

    def select(
        self,
        intent: str,
        project_slug: str,
        executor: PrimaryExecutor,
        requested_capabilities: list[str] | None = None,
    ) -> CapabilityReceipt:
        """Selects verified capabilities mapped from declared intent.

        Never grants arbitrary tool strings from untrusted user text or free-form prompts.
        Generates a CapabilityReceipt recording selected and denied capability ids.
        """
        normalized_intent = intent.strip().lower()
        selected_ids: list[str] = []
        denied_ids: list[str] = []

        import re

        # Find matching declared capabilities based on intent (word boundary)
        for cap_key, cap_profile in self.capabilities.items():
            if re.search(rf"\b{re.escape(cap_key)}\b", normalized_intent):
                cap_id = cap_profile.get("id", f"cap-{cap_key}")
                if cap_id not in selected_ids:
                    selected_ids.append(cap_id)

        # Detect any forbidden tool tokens in untrusted intent string and record them as denied
        for token in self.FORBIDDEN_TOOL_TOKENS:
            if re.search(rf"\b{re.escape(token)}\b", normalized_intent) and token not in denied_ids:
                denied_ids.append(token)

        # Check explicitly requested capabilities against allowlist
        if requested_capabilities:
            for req in requested_capabilities:
                try:
                    resolved = self.resolve_requested_capability(req)
                    res_id = resolved.get("id", req)
                    if res_id in selected_ids:
                        continue
                    # If resolved but intent does not justify it, record as denied
                    if res_id not in denied_ids:
                        denied_ids.append(res_id)
                except UnknownCapability:
                    if req not in denied_ids:
                        denied_ids.append(req)

        # If intent matched nothing, record declared intent itself in denied list
        if not selected_ids and intent not in denied_ids:
            denied_ids.append(intent)

        return CapabilityReceipt(
            registry_version=self.registry_version,
            mission_intent=intent,
            selected_capability_ids=selected_ids,
            denied_capability_ids=denied_ids,
            selected_at=datetime.now(timezone.utc),
        )


__all__ = ["CapabilityRegistry", "UnknownCapability"]
