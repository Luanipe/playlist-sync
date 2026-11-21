"""Tests that the CI workflow runs lint, types and tests on the required matrix."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"

REQUIRED_OS = {"ubuntu-latest", "windows-latest"}
REQUIRED_PYTHON = {"3.11", "3.12", "3.13"}


def _workflow() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _triggers(workflow: dict[Any, Any]) -> dict[Any, Any]:
    # PyYAML parses the unquoted `on:` key as the boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    return triggers


def test_workflow_runs_on_push_and_pull_request() -> None:
    triggers = _triggers(_workflow())
    assert "push" in triggers
    assert "pull_request" in triggers


def test_matrix_covers_supported_os_and_python_versions() -> None:
    matrix = _workflow()["jobs"]["checks"]["strategy"]["matrix"]
    assert set(matrix["os"]) == REQUIRED_OS
    assert set(matrix["python-version"]) == REQUIRED_PYTHON


def test_steps_run_lint_types_and_tests() -> None:
    steps = _workflow()["jobs"]["checks"]["steps"]
    commands = "\n".join(str(step.get("run", "")) for step in steps)
    assert "ruff check" in commands
    assert "ruff format --check" in commands
    assert "mypy" in commands
    assert "pytest" in commands
