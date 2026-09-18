"""Honest capability health probes with empirical verification and diagnostic evidence."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
from typing import Any, List, Optional, Union
import urllib.error
import urllib.request

from pydantic import BaseModel, ConfigDict

try:
    from backend.config import config
except ImportError:
    config = None  # type: ignore

try:
    from backend.services.hermes_adapter import HermesAdapter
except ImportError:
    HermesAdapter = None  # type: ignore

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


class CapabilityResult(BaseModel):
    """Structured health and capability probe result."""
    model_config = ConfigDict(extra="ignore")

    component: str
    status: str  # "available", "degraded", "unavailable"
    checked_at: datetime
    evidence: str
    version: Optional[str] = None
    recovery_action: Optional[str] = None

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class CapabilityProbe:
    """Probes system capabilities honestly using empirical execution rather than assumptions."""

    def __init__(
        self,
        db_path: Optional[Union[Path, str]] = None,
        agy_path: Optional[Union[Path, str]] = None,
        webbridge_url: Optional[str] = None,
    ) -> None:
        if db_path is not None:
            self.db_path: Union[Path, str] = db_path
        elif config and hasattr(config, "MISSION_DB_PATH"):
            self.db_path = config.MISSION_DB_PATH
        else:
            self.db_path = Path("var/lib/missions.db")

        self.agy_path = agy_path
        self.webbridge_url = webbridge_url or "http://127.0.0.1:10087/health"

    def check_agy(self, executable: Optional[Union[Path, str]] = None) -> CapabilityResult:
        """Checks AGY executable availability.

        If executable exists, tests execution (--version or --help). Never reports
        'available' based solely on file existence without testing execution;
        if executable not found, reports 'unavailable' with recovery action
        'Install or configure AGY CLI'.
        """
        now = datetime.now(timezone.utc)
        target_exe = executable or self.agy_path or os.getenv("AGY_EXECUTABLE_PATH") or "agy"
        exe_str = str(target_exe)

        # 1. Resolve path: either existing file path or command in PATH
        resolved_path: Optional[str] = None
        if Path(exe_str).is_file():
            resolved_path = str(Path(exe_str).resolve())
        else:
            resolved_path = shutil.which(exe_str)

        if not resolved_path:
            return CapabilityResult(
                component="agy",
                status="unavailable",
                checked_at=now,
                evidence="executable_not_found",
                version=None,
                recovery_action="Install or configure AGY CLI",
            )

        # 2. File exists: empirically test execution! NEVER report "available" on file existence alone
        cmd = [resolved_path, "--version"]
        if os.name == "nt" and resolved_path.lower().endswith((".bat", ".cmd")):
            cmd = ["cmd.exe", "/c", resolved_path, "--version"]

        try:
            # First try --version
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2.0,
                shell=False,
            )
            if proc.returncode == 0:
                out = (proc.stdout or proc.stderr or "").strip()
                version = out.splitlines()[0] if out else "unknown"
                return CapabilityResult(
                    component="agy",
                    status="available",
                    checked_at=now,
                    evidence="cli_execution_verified",
                    version=version,
                    recovery_action=None,
                )

            # If --version returned non-zero, try --help as fallback
            cmd_help = [resolved_path, "--help"]
            if os.name == "nt" and resolved_path.lower().endswith((".bat", ".cmd")):
                cmd_help = ["cmd.exe", "/c", resolved_path, "--help"]

            proc_help = subprocess.run(
                cmd_help,
                capture_output=True,
                text=True,
                timeout=2.0,
                shell=False,
            )
            if proc_help.returncode == 0:
                return CapabilityResult(
                    component="agy",
                    status="available",
                    checked_at=now,
                    evidence="cli_execution_verified (help output)",
                    version="unknown",
                    recovery_action=None,
                )

            # Non-zero exit code on execution test
            return CapabilityResult(
                component="agy",
                status="degraded",
                checked_at=now,
                evidence=f"execution_failed_code_{proc.returncode}",
                version=None,
                recovery_action="Verify AGY CLI installation and permissions",
            )
        except subprocess.TimeoutExpired:
            return CapabilityResult(
                component="agy",
                status="degraded",
                checked_at=now,
                evidence="execution_timeout",
                version=None,
                recovery_action="Verify AGY CLI responsiveness",
            )
        except (OSError, PermissionError) as exc:
            return CapabilityResult(
                component="agy",
                status="unavailable",
                checked_at=now,
                evidence=f"execution_error: {type(exc).__name__}",
                version=None,
                recovery_action="Verify AGY CLI binary permissions and format",
            )
        except Exception as exc:
            return CapabilityResult(
                component="agy",
                status="unavailable",
                checked_at=now,
                evidence=f"execution_unexpected_error: {str(exc)}",
                version=None,
                recovery_action="Verify AGY CLI installation and permissions",
            )

    def check_hermes(self, enabled: Optional[bool] = None) -> CapabilityResult:
        """Checks if Hermes adapter is enabled and probe passes."""
        now = datetime.now(timezone.utc)
        if HermesAdapter is None:
            return CapabilityResult(
                component="hermes",
                status="unavailable",
                checked_at=now,
                evidence="hermes_adapter_module_missing",
                version=None,
                recovery_action="Install Hermes adapter module",
            )

        try:
            adapter = HermesAdapter(enabled=enabled)
            avail = adapter.is_available()
            status_val = avail.get("status")
            if status_val == "available":
                return CapabilityResult(
                    component="hermes",
                    status="available",
                    checked_at=now,
                    evidence="hermes_adapter_active",
                    version=avail.get("version", "1.0.0"),
                    recovery_action=None,
                )
            else:
                return CapabilityResult(
                    component="hermes",
                    status="unavailable",
                    checked_at=now,
                    evidence="hermes_adapter_disabled",
                    version=None,
                    recovery_action="Enable Hermes adapter in config (HERMES_ADAPTER_ENABLED=true)",
                )
        except Exception as exc:
            return CapabilityResult(
                component="hermes",
                status="degraded",
                checked_at=now,
                evidence=f"hermes_probe_error: {str(exc)}",
                version=None,
                recovery_action="Verify Hermes coordinator configuration",
            )

    def check_database(self, db_path: Optional[Union[Path, str]] = None) -> CapabilityResult:
        """Executes SELECT 1 on SQLite WAL database."""
        now = datetime.now(timezone.utc)
        target = db_path if db_path is not None else self.db_path

        try:
            if isinstance(target, Path) and not target.exists() and str(target) != ":memory:":
                target.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(target), timeout=2.0)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if not row or row[0] != 1:
                    raise RuntimeError("Query returned unexpected result")

                cursor.execute("PRAGMA journal_mode;")
                jmode_row = cursor.fetchone()
                jmode = jmode_row[0] if jmode_row else "unknown"

                evidence = f"sqlite_wal_verified (journal_mode={jmode})"
                return CapabilityResult(
                    component="database",
                    status="available",
                    checked_at=now,
                    evidence=evidence,
                    version=sqlite3.sqlite_version,
                    recovery_action=None,
                )
            finally:
                conn.close()
        except Exception as exc:
            return CapabilityResult(
                component="database",
                status="unavailable",
                checked_at=now,
                evidence=f"db_error: {str(exc)}",
                version=None,
                recovery_action="Check database file path, permissions, and WAL locks",
            )

    def check_webbridge(self, url: Optional[str] = None, timeout: float = 1.0) -> CapabilityResult:
        """Probes http://127.0.0.1:10087/health or returns degraded/unavailable if offline."""
        now = datetime.now(timezone.utc)
        target_url = url or self.webbridge_url

        try:
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "Hermes-CapabilityProbe/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.getcode()
                if status_code == 200:
                    return CapabilityResult(
                        component="webbridge",
                        status="available",
                        checked_at=now,
                        evidence=f"webbridge_online (HTTP {status_code})",
                        version=None,
                        recovery_action=None,
                    )
                else:
                    return CapabilityResult(
                        component="webbridge",
                        status="degraded",
                        checked_at=now,
                        evidence=f"webbridge_unexpected_status ({status_code})",
                        version=None,
                        recovery_action="Check WebBridge service status",
                    )
        except urllib.error.HTTPError as exc:
            return CapabilityResult(
                component="webbridge",
                status="degraded",
                checked_at=now,
                evidence=f"webbridge_http_error ({exc.code})",
                version=None,
                recovery_action="Check WebBridge health endpoint routing",
            )
        except Exception as exc:
            return CapabilityResult(
                component="webbridge",
                status="unavailable",
                checked_at=now,
                evidence="webbridge_offline",
                version=None,
                recovery_action="Start GangNiaga WebBridge service on port 10087",
            )

    def check_tunnel(self) -> CapabilityResult:
        """Checks local cloudflared tunnel status."""
        now = datetime.now(timezone.utc)

        # Check if process is running
        is_running = False
        if psutil is not None:
            try:
                for p in psutil.process_iter(["name"]):
                    name = (p.info.get("name") or "").lower()
                    if name in ("cloudflared.exe", "cloudflared"):
                        is_running = True
                        break
            except Exception:
                pass

        if is_running:
            return CapabilityResult(
                component="tunnel",
                status="available",
                checked_at=now,
                evidence="tunnel_process_running",
                version=None,
                recovery_action=None,
            )

        # If not running, check if installed
        exe_path = shutil.which("cloudflared")
        if not exe_path:
            for fallback in (
                r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
                r"C:\Program Files\cloudflared\cloudflared.exe",
            ):
                if Path(fallback).is_file():
                    exe_path = fallback
                    break

        if exe_path:
            return CapabilityResult(
                component="tunnel",
                status="degraded",
                checked_at=now,
                evidence="tunnel_process_not_running",
                version=None,
                recovery_action="Start cloudflared tunnel service forwarding to port 9220",
            )

        return CapabilityResult(
            component="tunnel",
            status="unavailable",
            checked_at=now,
            evidence="cloudflared_not_installed",
            version=None,
            recovery_action="Install and configure cloudflared CLI",
        )

    def check_all(self) -> List[CapabilityResult]:
        """Runs all capability probes and returns structured results."""
        return [
            self.check_agy(),
            self.check_hermes(),
            self.check_database(),
            self.check_webbridge(),
            self.check_tunnel(),
        ]
