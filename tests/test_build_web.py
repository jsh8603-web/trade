"""Build integrity tests for web/HTML asset references (B5팀).

Verifies that relative paths referenced in HTML files (src, href, srcset) actually
exist on the filesystem. CDN links (http://, https://, //) are skipped.

Scope:
- scripts/web_server.py served content
- data/*.html
- index.html (project root)
- templates/, static/, assets/ HTML files (if present)
- web/, tools/ HTML files

Excluded:
- .venv/, node_modules/, .git/, .claude/, tmp/
- Backup files (*.bak, *.old)

Dependencies:
- BeautifulSoup4 preferred; falls back to regex if bs4 is missing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple
from urllib.parse import unquote, urlparse

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to skip entirely while scanning for HTML files.
EXCLUDED_DIR_PARTS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    ".claude",
    ".playwright-mcp",
    "tmp",
    "__pycache__",
    "CCimages",
    "htmlcov",
    "site-packages",
}

# Allowed URI schemes that are "external" and should be skipped.
EXTERNAL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

# Attributes that carry resource URLs in HTML.
REF_ATTRS = ("src", "href", "srcset", "poster", "data-src")


def _is_excluded(path: Path) -> bool:
    """Return True if path is inside an excluded directory or is a backup file."""
    parts = set(path.parts)
    if parts & EXCLUDED_DIR_PARTS:
        return True
    name = path.name.lower()
    if name.endswith(".bak") or name.endswith(".old") or name.endswith(".orig"):
        return True
    return False


def _collect_html_files() -> List[Path]:
    """Find all HTML files under the project root (honouring exclusions)."""
    html_files: List[Path] = []
    for p in PROJECT_ROOT.rglob("*.html"):
        if _is_excluded(p.relative_to(PROJECT_ROOT)):
            continue
        # Guard again at absolute level (in case rglob surfaces odd paths).
        if _is_excluded(p):
            continue
        html_files.append(p)
    return sorted(html_files)


def _is_external_or_placeholder(ref: str) -> bool:
    """Return True for URLs that should be skipped (CDN, data, mailto, anchors, templated)."""
    if not ref:
        return True
    ref = ref.strip()
    if not ref:
        return True
    # Protocol-relative (//cdn.example.com/...) -> external.
    if ref.startswith("//"):
        return True
    # Pure anchor or query fragment.
    if ref.startswith("#") or ref.startswith("?"):
        return True
    # Absolute path from web root - treat as non-filesystem reference. Many
    # such paths are server-side routes (Flask endpoints) that do not map to
    # filesystem paths, so we skip them instead of flagging as broken.
    if ref.startswith("/"):
        return True
    # Any URI with an explicit scheme (http, https, data, mailto, javascript, file, ...).
    if EXTERNAL_SCHEME_RE.match(ref):
        return True
    # Templated placeholders (Jinja, Flask url_for, JS template literals, etc.).
    if "{{" in ref or "}}" in ref or "{%" in ref or "${" in ref:
        return True
    return False


def _split_srcset(value: str) -> List[str]:
    """Split a srcset attribute into individual URL candidates."""
    urls: List[str] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        # Each candidate is "URL [descriptor]"; take the URL token only.
        urls.append(part.split()[0])
    return urls


def _extract_refs_bs4(html_text: str) -> List[Tuple[str, str]]:
    """Extract (attribute, value) pairs using BeautifulSoup."""
    from bs4 import BeautifulSoup  # type: ignore

    soup = BeautifulSoup(html_text, "html.parser")
    refs: List[Tuple[str, str]] = []
    for tag in soup.find_all(True):
        for attr in REF_ATTRS:
            if not tag.has_attr(attr):
                continue
            val = tag.get(attr)
            if not isinstance(val, str):
                continue
            if attr == "srcset":
                for url in _split_srcset(val):
                    refs.append((attr, url))
            else:
                refs.append((attr, val))
    return refs


_REGEX_REF = re.compile(
    r"""(src|href|srcset|poster|data-src)\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)


def _extract_refs_regex(html_text: str) -> List[Tuple[str, str]]:
    """Fallback regex extractor when bs4 is unavailable."""
    refs: List[Tuple[str, str]] = []
    for m in _REGEX_REF.finditer(html_text):
        attr = m.group(1).lower()
        val = m.group(2)
        if attr == "srcset":
            for url in _split_srcset(val):
                refs.append((attr, url))
        else:
            refs.append((attr, val))
    return refs


def _extract_refs(html_text: str) -> List[Tuple[str, str]]:
    try:
        import bs4  # noqa: F401

        return _extract_refs_bs4(html_text)
    except Exception:
        return _extract_refs_regex(html_text)


def _normalize_ref(ref: str) -> str:
    """Strip query/fragment and URL-decode a relative reference."""
    parsed = urlparse(ref)
    path = parsed.path or ref
    return unquote(path)


def _resolve_ref(html_file: Path, ref: str) -> Path:
    """Resolve a relative reference against the HTML file's directory."""
    normalized = _normalize_ref(ref)
    return (html_file.parent / normalized).resolve()


# ---------------------------------------------------------------------------
# Test collection
# ---------------------------------------------------------------------------

HTML_FILES = _collect_html_files()
HTML_IDS = [str(p.relative_to(PROJECT_ROOT)).replace("\\", "/") for p in HTML_FILES]


def test_html_files_discovered():
    """Sanity check: at least the root index.html should be present."""
    root_index = PROJECT_ROOT / "index.html"
    assert root_index.exists(), "Project root index.html missing"
    assert root_index in HTML_FILES, (
        "Root index.html was excluded by the scanner; check exclusion rules"
    )


@pytest.mark.parametrize(
    "html_file",
    HTML_FILES,
    ids=HTML_IDS or ["<no-html-files>"],
)
def test_html_asset_references_exist(html_file: Path) -> None:
    """All relative asset references in an HTML file must resolve to a real file."""
    try:
        html_text = html_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        pytest.skip(f"Cannot read {html_file}: {exc}")

    refs = _extract_refs(html_text)

    missing: List[str] = []
    for attr, raw in refs:
        if _is_external_or_placeholder(raw):
            continue
        resolved = _resolve_ref(html_file, raw)
        # Only flag paths that fall inside the project root - external relative
        # paths (e.g. "../../elsewhere") that escape the repo are ignored.
        try:
            resolved.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if not resolved.exists():
            missing.append(f"{attr}={raw!r} -> {resolved}")

    rel = html_file.relative_to(PROJECT_ROOT)
    assert not missing, (
        f"Broken relative references in {rel}:\n  " + "\n  ".join(missing)
    )
