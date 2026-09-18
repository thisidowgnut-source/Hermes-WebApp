"""Static UI contracts for the acceptance criteria in TODO.md.

These checks intentionally avoid a browser so they can run as a fast,
deterministic regression gate while the UI is being refactored.
"""

from __future__ import annotations

from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"

VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class _MarkupParser(HTMLParser):
    """Small HTML contract parser with enough structure for static checks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[dict[str, object]] = []
        self.stack: list[str] = []
        self.mismatches: list[str] = []

    def _record_element(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        self.elements.append(
            {
                "tag": tag.lower(),
                "attrs": attributes,
                "line": self.getpos()[0],
                "ancestors": tuple(self.stack),
            }
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        self._record_element(normalized_tag, attrs)
        if normalized_tag not in VOID_ELEMENTS:
            self.stack.append(normalized_tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record_element(tag.lower(), attrs)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in VOID_ELEMENTS:
            return
        if not self.stack:
            self.mismatches.append(f"line {self.getpos()[0]}: unexpected </{normalized_tag}>")
            return
        if self.stack[-1] == normalized_tag:
            self.stack.pop()
            return

        self.mismatches.append(
            f"line {self.getpos()[0]}: expected </{self.stack[-1]}> before </{normalized_tag}>"
        )
        if normalized_tag in self.stack:
            while self.stack and self.stack[-1] != normalized_tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()


def _load_index() -> tuple[str, _MarkupParser]:
    source = INDEX_HTML.read_text(encoding="utf-8")
    parser = _MarkupParser()
    parser.feed(source)
    parser.close()
    return source, parser


def _css_rule(source: str, selector: str) -> str:
    pattern = rf"(?<![\w.-]){re.escape(selector)}(?![\w.-])\s*\{{([^{{}}]*)\}}"
    match = re.search(pattern, source, flags=re.IGNORECASE | re.DOTALL)
    assert match, f"Missing CSS rule for {selector!r}"
    return match.group(1)


def _css_value(rule: str, property_name: str) -> str:
    match = re.search(
        rf"(?:^|;)\s*{re.escape(property_name)}\s*:\s*([^;]+)",
        rule,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip().lower() if match else ""


def _elements(parser: _MarkupParser, tag: str) -> list[dict[str, object]]:
    return [element for element in parser.elements if element["tag"] == tag]


def test_module_overlay_css_has_explicit_hidden_and_active_states() -> None:
    source, _ = _load_index()
    inactive = _css_rule(source, ".module-overlay")
    active = _css_rule(source, ".module-overlay.active")

    assert _css_value(inactive, "visibility") == "hidden"
    assert "translate" in _css_value(inactive, "transform")
    assert _css_value(inactive, "pointer-events") == "none"

    assert _css_value(active, "visibility") == "visible"
    assert "translatey(0" in _css_value(active, "transform").replace(" ", "")
    assert _css_value(active, "pointer-events") == "auto"


def test_module_overlays_have_dialog_semantics_and_hidden_initial_state() -> None:
    _, parser = _load_index()
    overlays = [
        element
        for element in parser.elements
        if "module-overlay" in str(element["attrs"].get("class", "")).split()
    ]
    assert overlays, "Expected module overlays in static/index.html"

    active_overlays = [
        element
        for element in overlays
        if "active" in str(element["attrs"].get("class", "")).split()
    ]
    assert not active_overlays, "Module overlays must not be active in the initial HTML"

    invalid = []
    for element in overlays:
        attrs = element["attrs"]
        if attrs.get("role") != "dialog":
            invalid.append(f"line {element['line']}: role={attrs.get('role')!r}")
        if attrs.get("aria-modal") != "true":
            invalid.append(f"line {element['line']}: aria-modal={attrs.get('aria-modal')!r}")
        if attrs.get("aria-hidden") != "true":
            invalid.append(f"line {element['line']}: aria-hidden={attrs.get('aria-hidden')!r}")
    assert not invalid, "Invalid module overlay semantics: " + "; ".join(invalid)


def test_viewport_meta_does_not_lock_zoom() -> None:
    _, parser = _load_index()
    viewport_tags = [
        element
        for element in _elements(parser, "meta")
        if element["attrs"].get("name", "").lower() == "viewport"
    ]
    assert viewport_tags, "Expected a viewport meta tag"

    content = " ".join(str(element["attrs"].get("content", "")) for element in viewport_tags)
    assert not re.search(r"(?:^|,)\s*user-scalable\s*=\s*no\b", content, re.IGNORECASE)
    assert not re.search(r"(?:^|,)\s*maximum-scale\s*=\s*1(?:\.0+)?\b", content, re.IGNORECASE)


def test_form_controls_have_programmatic_labels() -> None:
    _, parser = _load_index()
    elements = parser.elements
    ids = {str(element["attrs"].get("id")) for element in elements if element["attrs"].get("id")}
    label_targets = {
        str(element["attrs"].get("for"))
        for element in _elements(parser, "label")
        if element["attrs"].get("for")
    }

    missing = []
    for element in elements:
        if element["tag"] not in {"input", "textarea", "select"}:
            continue
        attrs = element["attrs"]
        if element["tag"] == "input" and attrs.get("type", "text").lower() == "hidden":
            continue
        control_id = attrs.get("id", "")
        labelled = (
            bool(attrs.get("aria-label"))
            or bool(attrs.get("aria-labelledby"))
            or (bool(control_id) and control_id in label_targets)
            or "label" in element["ancestors"]
        )
        if not labelled:
            missing.append(f"line {element['line']}: <{element['tag']} id={control_id!r}>")

    assert not missing, "Unlabelled form controls: " + "; ".join(missing)
    unresolved_label_targets = sorted(label_targets - ids)
    assert not unresolved_label_targets, f"Labels reference missing control IDs: {unresolved_label_targets}"


def test_ids_are_unique_and_markup_is_balanced() -> None:
    _, parser = _load_index()
    ids: defaultdict[str, list[int]] = defaultdict(list)
    for element in parser.elements:
        element_id = element["attrs"].get("id")
        if element_id:
            ids[str(element_id)].append(int(element["line"]))

    duplicates = {element_id: lines for element_id, lines in ids.items() if len(lines) > 1}
    assert not duplicates, f"Duplicate IDs: {duplicates}"
    assert not parser.mismatches, "Malformed closing tags: " + "; ".join(parser.mismatches)
    assert not parser.stack, f"Unclosed HTML elements at EOF: {parser.stack}"


def test_dom_patch_does_not_strip_inline_handlers_or_assume_an_icon() -> None:
    source, _ = _load_index()
    assert "removeAttribute('onclick')" not in source
    assert 'removeAttribute("onclick")' not in source
    assert not re.search(r"querySelector\(\s*['\"]i['\"]\s*\)\.getAttribute\(", source)


def test_javascript_syntax_integrity() -> None:
    """Validate that every inline script in index.html parses cleanly without SyntaxError."""
    import subprocess
    import tempfile

    source, _ = _load_index()
    scripts = re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", source, re.DOTALL | re.IGNORECASE)
    assert len(scripts) > 0, "No inline scripts found in index.html"

    for i, script_body in enumerate(scripts):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(script_body)
            temp_path = f.name
        try:
            res = subprocess.run(["node", "-c", temp_path], capture_output=True, text=True)
            assert res.returncode == 0, f"Inline script #{i} has syntax error: {res.stderr}"
        finally:
            Path(temp_path).unlink(missing_ok=True)


