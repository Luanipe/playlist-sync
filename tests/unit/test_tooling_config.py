"""Tests that the tooling configuration matches the project rules.

These guard against a future edit silently dropping the strict typing for
``domain/`` and ``core/`` or changing where pytest looks for tests.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _config() -> dict[str, Any]:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


def test_mypy_is_strict_for_domain_and_core() -> None:
    overrides = _config()["tool"]["mypy"]["overrides"]
    strict_modules = {
        module
        for override in overrides
        if override.get("strict") is True
        for module in override.get("module", [])
    }
    assert {"playlist_sync.domain.*", "playlist_sync.core.*"} <= strict_modules


def test_pytest_collects_from_tests_dir() -> None:
    assert _config()["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_ruff_targets_python_311() -> None:
    assert _config()["tool"]["ruff"]["target-version"] == "py311"
