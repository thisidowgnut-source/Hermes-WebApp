"""Project registry service for managing and validating project and agent profiles."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.config import config
from backend.models.mission import AgentProfile, OperatorContext, ProjectProfile

logger = logging.getLogger(__name__)


class ProjectRegistryError(Exception):
    """Base exception for all project registry errors."""
    pass


class ProjectNotFound(ProjectRegistryError):
    """Raised when a requested project slug is not found in the registry."""
    pass


class AgentProfileNotFound(ProjectRegistryError):
    """Raised when an agent key is not found in the project profile."""
    pass


class ProjectProfileError(ProjectRegistryError):
    """Raised when a project profile is invalid, corrupt, or unsafe."""
    pass


class ProjectRegistry:
    """Registry managing project configurations and their authorized agents."""

    def __init__(self, projects_dir: Path | str | None = None) -> None:
        if projects_dir is None:
            self.projects_dir = Path(config.PROJECTS_DIR)
        else:
            self.projects_dir = Path(projects_dir)

    def get(self, slug: str) -> ProjectProfile:
        """Retrieve and validate a project profile by its slug."""
        if not slug or not isinstance(slug, str):
            raise ProjectNotFound(f"Invalid project slug: {slug}")

        clean_slug = slug.strip()
        if ".." in clean_slug or "/" in clean_slug or "\\" in clean_slug:
            raise ProjectNotFound(f"Project not found: {slug}")

        file_path = self.projects_dir / f"{clean_slug}.json"
        if not file_path.is_file():
            raise ProjectNotFound(f"Project '{clean_slug}' not found at {file_path}")

        return self.load(file_path)

    def list_visible(self, operator: OperatorContext | None = None) -> list[ProjectProfile]:
        """List all valid project profiles in the configured projects directory."""
        if not self.projects_dir.exists() or not self.projects_dir.is_dir():
            return []

        profiles: list[ProjectProfile] = []
        for file_path in sorted(self.projects_dir.glob("*.json")):
            try:
                profile = self.load(file_path)
                profiles.append(profile)
            except Exception as e:
                logger.warning("Failed to load project profile %s: %s", file_path, e)
                continue
        return profiles

    def require_agent(self, project_slug: str, agent_key: str) -> AgentProfile:
        """Retrieve an agent profile or raise AgentProfileNotFound."""
        profile = self.get(project_slug)
        if agent_key not in profile.agents:
            raise AgentProfileNotFound(
                f"Agent '{agent_key}' not found in project '{project_slug}'. "
                f"Available agents: {list(profile.agents.keys())}"
            )
        return profile.agents[agent_key]

    @staticmethod
    def validate_workspace(profile: ProjectProfile) -> None:
        """Validate that workspace path is safe and does not target system roots."""
        if not profile.workspace_path:
            raise ProjectProfileError("workspace_path cannot be empty")

        raw_path_str = str(profile.workspace_path).strip()
        normalized_raw = raw_path_str.replace("\\", "/").lower()

        dangerous_raw_prefixes = (
            "c:/windows",
            "/windows",
            "c:/program files",
            "c:/program files (x86)",
            "c:/programdata",
        )
        for prefix in dangerous_raw_prefixes:
            if normalized_raw == prefix or normalized_raw.startswith(prefix + "/"):
                raise ProjectProfileError(
                    f"workspace_path points to dangerous system root: {profile.workspace_path}"
                )

        try:
            resolved = Path(profile.workspace_path).resolve()
        except Exception as e:
            raise ProjectProfileError(f"Invalid workspace_path: {e}") from e

        # Disallow filesystem or drive roots
        if resolved == Path(resolved.anchor) or str(resolved).rstrip("/\\") == resolved.anchor.rstrip("/\\"):
            raise ProjectProfileError(
                f"workspace_path cannot be a drive or root directory: {profile.workspace_path}"
            )

        resolved_str = str(resolved).replace("/", "\\").lower()

        dangerous_resolved_prefixes = (
            "c:\\windows",
            "\\windows",
            "/windows",
            "c:\\program files",
            "c:\\program files (x86)",
            "c:\\programdata",
            "c:\\system volume information",
            "c:\\$recycle.bin",
            "/etc",
            "/bin",
            "/sbin",
            "/usr",
            "/var",
            "/sys",
            "/proc",
            "/dev",
            "/boot",
            "/root",
        )
        for danger in dangerous_resolved_prefixes:
            danger_norm = danger.replace("/", "\\").lower()
            if resolved_str == danger_norm or resolved_str.startswith(danger_norm + "\\"):
                raise ProjectProfileError(
                    f"workspace_path points to dangerous system root: {profile.workspace_path}"
                )

    @staticmethod
    def validate_agent_definitions(profile: ProjectProfile) -> None:
        """Verify on-disk agent definitions when loading Doh-Nut project."""
        if profile.slug == "doh-nut":
            if profile.workspace_path.exists():
                agents_dir = profile.workspace_path / ".gemini" / "agents"
                if not agents_dir.is_dir():
                    raise ProjectProfileError(
                        f"Agent definitions directory missing at {agents_dir} for project '{profile.slug}'"
                    )
                for agent_key in profile.agents:
                    agent_file = agents_dir / f"{agent_key}.md"
                    if not agent_file.is_file():
                        raise ProjectProfileError(
                            f"Agent definition file for '{agent_key}' missing at {agent_file}"
                        )

            # Check brand truth file for doh-nut
            if profile.workspace_path.exists() and not profile.brand_truth_path.is_file():
                raise ProjectProfileError(
                    f"Brand truth file missing at {profile.brand_truth_path} for project '{profile.slug}'"
                )

    @staticmethod
    def load(file_path: Path | str) -> ProjectProfile:
        """Load and strictly validate a project profile JSON file."""
        path = Path(file_path)
        if not path.is_file():
            raise ProjectProfileError(f"Project profile file not found: {file_path}")

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception as e:
            raise ProjectProfileError(f"Failed to read project profile JSON from {file_path}: {e}") from e

        if not isinstance(data, dict):
            raise ProjectProfileError(f"Project profile JSON must be an object, got {type(data).__name__}")

        try:
            profile = ProjectProfile.model_validate(data)
        except Exception as e:
            raise ProjectProfileError(f"Invalid project profile schema in {file_path}: {e}") from e

        ProjectRegistry.validate_workspace(profile)
        ProjectRegistry.validate_agent_definitions(profile)
        return profile
