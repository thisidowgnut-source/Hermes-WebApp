"""Tests for CapabilityProbe health verification and empirical truthfulness."""
from datetime import datetime
from pathlib import Path
import sqlite3
import subprocess
from unittest.mock import patch, MagicMock
import pytest

from backend.services.capability_probe import CapabilityProbe, CapabilityResult


@pytest.fixture
def probe(tmp_path):
    db_file = tmp_path / "probe_test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("CREATE TABLE dummy (id INTEGER PRIMARY KEY);")
    conn.close()
    return CapabilityProbe(db_path=db_file)


def test_file_existence_is_not_reported_as_online(probe, tmp_path):
    """Fake file presence must NOT report available without empirical execution."""
    fake_agy_path = tmp_path / "fake_agy.exe"
    # Create a dummy file that exists but fails execution
    fake_agy_path.write_text("not-a-real-executable", encoding="utf-8")

    result = probe.check_agy(executable=fake_agy_path)
    assert result.status in {"available", "degraded", "unavailable"}
    assert result.checked_at is not None
    assert result.evidence != "file_exists_only"
    # Status cannot be "available" because execution failed
    assert result.status != "available"


def test_agy_executable_missing_reports_unavailable_with_recovery():
    probe = CapabilityProbe()
    result = probe.check_agy(executable="nonexistent_binary_for_test_12345")
    assert result.component == "agy"
    assert result.status == "unavailable"
    assert result.evidence == "executable_not_found"
    assert result.recovery_action == "Install or configure AGY CLI"
    assert result.version is None


def test_agy_successful_execution_reports_available(tmp_path):
    fake_exe = tmp_path / "mock_agy.exe"
    fake_exe.write_text("mock binary", encoding="utf-8")

    probe = CapabilityProbe(agy_path=fake_exe)
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "AGY CLI v1.8.4 (x86_64-windows)\n"
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        result = probe.check_agy(executable=fake_exe)
        assert result.component == "agy"
        assert result.status == "available"
        assert result.evidence == "cli_execution_verified"
        assert result.version == "AGY CLI v1.8.4 (x86_64-windows)"
        assert result.recovery_action is None


def test_hermes_probe_reflects_feature_flag(probe):
    # Probe when disabled
    disabled_result = probe.check_hermes(enabled=False)
    assert disabled_result.component == "hermes"
    assert disabled_result.status == "unavailable"
    assert "disabled" in disabled_result.evidence
    assert disabled_result.recovery_action is not None

    # Probe when enabled
    enabled_result = probe.check_hermes(enabled=True)
    assert enabled_result.component == "hermes"
    assert enabled_result.status == "available"
    assert enabled_result.version == "1.0.0"
    assert enabled_result.recovery_action is None


def test_database_probe_executes_select_1(probe):
    result = probe.check_database()
    assert result.component == "database"
    assert result.status == "available"
    assert "sqlite_wal_verified" in result.evidence
    assert result.version == sqlite3.sqlite_version
    assert result.recovery_action is None


def test_database_probe_reports_unavailable_on_failure(probe):
    bad_path = Path("Z:/impossible_drive/impossible_folder/test.db")
    result = probe.check_database(db_path=bad_path)
    assert result.component == "database"
    assert result.status == "unavailable"
    assert "db_error" in result.evidence
    assert result.recovery_action is not None


def test_webbridge_probe_offline(probe):
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        result = probe.check_webbridge(url="http://127.0.0.1:59998/health")
        assert result.component == "webbridge"
        assert result.status == "unavailable"
        assert "webbridge_offline" in result.evidence
        assert "Start GangNiaga WebBridge" in (result.recovery_action or "")


def test_webbridge_probe_online_mock(probe):
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = probe.check_webbridge()
        assert result.component == "webbridge"
        assert result.status == "available"
        assert "webbridge_online" in result.evidence
        assert result.recovery_action is None


def test_tunnel_probe_structure(probe):
    result = probe.check_tunnel()
    assert result.component == "tunnel"
    assert result.status in {"available", "degraded", "unavailable"}
    assert result.checked_at is not None
    assert result.evidence


def test_tunnel_probe_running_mock(probe):
    mock_proc = MagicMock()
    mock_proc.info = {"name": "cloudflared.exe"}

    with patch("psutil.process_iter", return_value=[mock_proc]):
        result = probe.check_tunnel()
        assert result.component == "tunnel"
        assert result.status == "available"
        assert result.evidence == "tunnel_process_running"


def test_check_all_returns_structured_results_for_all_components(probe):
    results = probe.check_all()
    assert isinstance(results, list)
    assert len(results) == 5

    components = [r.component for r in results]
    assert components == ["agy", "hermes", "database", "webbridge", "tunnel"]

    for r in results:
        assert isinstance(r, CapabilityResult)
        assert r.status in {"available", "degraded", "unavailable"}
        assert isinstance(r.checked_at, datetime)
        assert r.evidence
        # Dictionary-style access compatibility
        assert r["status"] == r.status
        assert r["component"] == r.component
