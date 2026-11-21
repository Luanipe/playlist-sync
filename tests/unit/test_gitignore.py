"""Tests that `.gitignore` covers the categories required by the roadmap."""

from __future__ import annotations

from pathlib import Path

GITIGNORE = Path(__file__).resolve().parents[2] / ".gitignore"

# Patterns the roadmap task explicitly calls out: venvs, *.db, .env, tokens,
# browser profiles, reports and fixtures with personal data (plus caches).
REQUIRED_PATTERNS = {
    ".venv/",
    "__pycache__/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".coverage",
    ".env",
    "*.db",
    "*.token",
    "tokens.json",
    "cookies.json",
    "browser-profile/",
    "reports/",
    "tests/fixtures/private/",
}


def _patterns() -> set[str]:
    lines = GITIGNORE.read_text(encoding="utf-8").splitlines()
    return {
        stripped for line in lines if (stripped := line.strip()) and not stripped.startswith("#")
    }


def test_gitignore_covers_required_patterns() -> None:
    assert REQUIRED_PATTERNS.issubset(_patterns())


def test_lockfile_is_not_ignored() -> None:
    assert "uv.lock" not in _patterns()
