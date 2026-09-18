"""Unit tests for ProjectRegistry service and project configuration."""
import json
from pathlib import Path
from uuid import uuid4
import pytest

from backend.models.mission import AgentProfile, OperatorContext, ProjectProfile
from backend.services.project_registry import (
    AgentProfileNotFound,
    ProjectNotFound,
    ProjectProfileError,
    ProjectRegistry,
)

EXPECTED_AGENT_KEYS = {
    "dohnut-orchestrator",
    "dohnut-frontend-artisan",
    "dohnut-backend-architect",
    "dohnut-realtime-ops",
    "dohnut-qa-guardian",
    "dohnut-brand-guardian",
    "dohnut-viral-engine",
    "dohnut-social-autopilot",
}


def write_profile(dir_path: Path, workspace_path: str = "G:/Doh-Nut", slug: str = "test-project", **kwargs) -> Path:
    """Helper to write a project profile JSON into a directory."""
    data = {
        "slug": slug,
        "display_name": kwargs.get("display_name", "Test Project"),
        "workspace_path": workspace_path,
        "agy_project_id": kwargs.get("agy_project_id", None),
        "brand_truth_path": kwargs.get("brand_truth_path", "G:/Doh-Nut/brand-system/01-brand-truth.md"),
        "approval_policy": kwargs.get("approval_policy", {
            "social_requires_human_confirmation": True,
            "approval_ttl_seconds": 900,
        }),
        "agents": kwargs.get("agents", {
            "test-agent": {"display_name": "Test Agent", "execution": "agy"}
        }),
    }
    file_path = dir_path / f"{slug}.json"
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return file_path


def test_dohnut_profile_resolves_existing_workspace_and_all_agents():
    registry = ProjectRegistry()
    profile = registry.get("doh-nut")
    assert isinstance(profile, ProjectProfile)
    assert profile.slug == "doh-nut"
    assert profile.display_name == "Doh-Nut"
    assert profile.workspace_path == Path("G:/Doh-Nut")
    assert set(profile.agents.keys()) == EXPECTED_AGENT_KEYS
    assert profile.agy_project_id is None
    assert profile.brand_truth_path == Path("G:/Doh-Nut/brand-system/01-brand-truth.md")
    assert profile.approval_policy.social_requires_human_confirmation is True
    assert profile.approval_policy.approval_ttl_seconds == 900


def test_unknown_project_and_agent_are_rejected():
    registry = ProjectRegistry()
    with pytest.raises(ProjectNotFound):
        registry.get("not-a-project")

    with pytest.raises(ProjectNotFound):
        registry.get("../../escape-attempt")

    with pytest.raises(AgentProfileNotFound):
        registry.require_agent("doh-nut", "shell-injection")

    with pytest.raises(ProjectNotFound):
        registry.require_agent("nonexistent-project", "dohnut-orchestrator")


def test_workspace_must_stay_inside_allowlisted_project_root(tmp_path):
    invalid = write_profile(tmp_path, workspace_path="C:/Windows")
    with pytest.raises(ProjectProfileError, match="workspace_path"):
        ProjectRegistry.load(invalid)

    invalid_sub = write_profile(tmp_path, slug="sub-win", workspace_path="C:/Windows/System32")
    with pytest.raises(ProjectProfileError, match="workspace_path"):
        ProjectRegistry.load(invalid_sub)

    invalid_root = write_profile(tmp_path, slug="drive-root", workspace_path="C:/")
    with pytest.raises(ProjectProfileError, match="workspace_path"):
        ProjectRegistry.load(invalid_root)


def test_list_visible_returns_loaded_profiles():
    registry = ProjectRegistry()
    operator = OperatorContext(operator_id=123456789, session_id=uuid4())
    profiles = registry.list_visible(operator)

    assert len(profiles) >= 1
    dohnut = next((p for p in profiles if p.slug == "doh-nut"), None)
    assert dohnut is not None
    assert dohnut.workspace_path == Path("G:/Doh-Nut")
    assert set(dohnut.agents.keys()) == EXPECTED_AGENT_KEYS


def test_list_visible_with_custom_directory_and_fault_tolerance(tmp_path):
    write_profile(tmp_path, slug="project-one", workspace_path="G:/Doh-Nut")
    write_profile(tmp_path, slug="project-two", workspace_path="G:/Doh-Nut")

    # Add a corrupted JSON file
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{bad json syntax", encoding="utf-8")

    registry = ProjectRegistry(projects_dir=tmp_path)
    profiles = registry.list_visible()
    assert len(profiles) == 2
    slugs = {p.slug for p in profiles}
    assert slugs == {"project-one", "project-two"}


def test_require_agent_success():
    registry = ProjectRegistry()
    agent = registry.require_agent("doh-nut", "dohnut-orchestrator")
    assert isinstance(agent, AgentProfile)
    assert agent.display_name == "Doh-Nut Orchestrator"
    assert agent.execution == "agy"


def test_malformed_json_raises_project_profile_error(tmp_path):
    corrupt_file = tmp_path / "malformed.json"
    corrupt_file.write_text("not json at all", encoding="utf-8")

    with pytest.raises(ProjectProfileError):
        ProjectRegistry.load(corrupt_file)


def test_missing_file_raises_project_profile_error():
    with pytest.raises(ProjectProfileError):
        ProjectRegistry.load("nonexistent_path_to_profile.json")
