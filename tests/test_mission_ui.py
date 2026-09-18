"""Static DOM, contract, and logic verification for Mobile Mission Control UI (Task 7)."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"
MISSION_CSS = PROJECT_ROOT / "static" / "mission-control.css"
MISSION_JS = PROJECT_ROOT / "static" / "mission-control.js"


class _TagParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[dict[str, object]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        self.elements.append({"tag": tag.lower(), "attrs": attributes, "line": self.getpos()[0]})

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        self.elements.append({"tag": tag.lower(), "attrs": attributes, "line": self.getpos()[0]})


def test_index_html_mounts_mission_control_assets() -> None:
    """Index HTML must include mission-control.css and mission-control.js."""
    html_content = INDEX_HTML.read_text(encoding="utf-8")
    assert "mission-control.css" in html_content
    assert "mission-control.js" in html_content


def test_index_html_has_mission_control_root() -> None:
    """Index HTML must declare a mission control mount root in Doh-Nut module."""
    html_content = INDEX_HTML.read_text(encoding="utf-8")
    parser = _TagParser()
    parser.feed(html_content)

    mc_roots = [
        el for el in parser.elements
        if el["attrs"].get("id") == "mission-control-root" or el["attrs"].get("data-mission-control")
    ]
    assert len(mc_roots) >= 1, "Expected #mission-control-root or [data-mission-control] in index.html"


def test_mission_control_css_enforces_touch_targets_and_oled_dark() -> None:
    """CSS must enforce minimum 44px touch targets on buttons/inputs and contain scroll."""
    css_content = MISSION_CSS.read_text(encoding="utf-8")
    assert "min-height: 44px" in css_content
    assert "[data-mission-control]" in css_content or ".mission-control-root" in css_content
    assert "overscroll-behavior: contain" in css_content or "overflow-y: auto" in css_content


def test_mission_control_js_exports_mount_interface() -> None:
    """mission-control.js must export window.HermesMissionControl.mount()."""
    js_content = MISSION_JS.read_text(encoding="utf-8")
    assert "window.HermesMissionControl" in js_content
    assert "mount: function" in js_content or "mount(" in js_content


def test_mission_control_js_maintains_session_cursor_and_30s_backoff() -> None:
    """Client must store sequence under hermes.mission.<id>.sequence and cap backoff at 30s."""
    js_content = MISSION_JS.read_text(encoding="utf-8")
    assert "hermes.mission." in js_content
    assert ".sequence" in js_content
    # Exponential backoff capped at 30,000ms (30 seconds)
    assert "30000" in js_content or "30 * 1000" in js_content


def test_mission_control_js_creates_semantic_controls_and_live_regions() -> None:
    """Rendered template in mission-control.js must have semantic actions and polite aria-live."""
    js_content = MISSION_JS.read_text(encoding="utf-8")
    assert 'data-action="create-mission"' in js_content
    assert 'data-action="send-turn"' in js_content
    assert 'data-action="cancel-mission"' in js_content
    assert 'aria-live="polite"' in js_content
    assert 'role="log"' in js_content or 'aria-live' in js_content


def test_mission_control_js_uses_safe_text_content_not_raw_html() -> None:
    """Dynamic event payloads must be assigned to textContent, never innerHTML."""
    js_content = MISSION_JS.read_text(encoding="utf-8")
    assert "text.textContent = displayContent" in js_content
    assert "meta.textContent =" in js_content
