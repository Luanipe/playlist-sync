"""Tests for the repository skeleton documentation files (README, CONTRIBUTING, LICENSE)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_readme_has_identity_status_and_disclaimer() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "# playlist-sync" in text
    assert "## Status" in text
    assert "## Disclaimer" in text


def test_contributing_documents_the_quality_gates() -> None:
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "Conventional Commits" in text
    for command in ("uv run ruff check", "uv run mypy", "uv run pytest"):
        assert command in text


def test_license_is_mit() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert text.startswith("MIT License")
    assert "Permission is hereby granted" in text
    assert "PLACEHOLDER" not in text.upper()
