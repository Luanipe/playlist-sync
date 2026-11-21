"""Tests for the autonomous-agent setup: opencode config, agents and commands."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT / ".opencode" / "agents"
COMMANDS_DIR = ROOT / ".opencode" / "commands"
ROADMAP = ROOT / "docs" / "ROADMAP.md"

EXPECTED_AGENTS = ("architect", "reviewer", "security-audit")
EXPECTED_COMMANDS = ("next-task", "autopilot", "check", "review", "security", "phase-report")


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    _, block, _ = text.split("---", 2)
    data = yaml.safe_load(block)
    assert isinstance(data, dict), path
    return data


def _rule(action: str, resource: str, effect: str) -> dict[str, str]:
    return {"action": action, "resource": resource, "effect": effect}


def _config() -> dict[str, Any]:
    return json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))


def test_config_uses_v2_permissions_and_instructions() -> None:
    config = _config()
    assert "permissions" in config
    assert "permission" not in config
    assert "bash" not in config
    assert "docs/ROADMAP.md" in config["instructions"]
    assert "docs/AGENT_WORKFLOW.md" in config["instructions"]


def test_commit_allowed_but_push_and_rm_denied() -> None:
    rules = _config()["permissions"]
    assert _rule("shell", "git commit *", "allow") in rules
    assert _rule("shell", "git push *", "deny") in rules
    assert _rule("shell", "rm -rf *", "deny") in rules


def test_expected_agents_exist_and_are_read_only() -> None:
    for name in EXPECTED_AGENTS:
        frontmatter = _frontmatter(AGENTS_DIR / f"{name}.md")
        assert frontmatter["mode"] == "subagent"
        assert "tools" not in frontmatter
        assert "temperature" not in frontmatter
        assert _rule("edit", "*", "deny") in frontmatter["permissions"]


def test_expected_commands_exist() -> None:
    for name in EXPECTED_COMMANDS:
        assert (COMMANDS_DIR / f"{name}.md").is_file(), name


def test_legacy_opencode_directories_are_gone() -> None:
    assert not (ROOT / ".opencode" / "agent").exists()
    assert not (ROOT / ".opencode" / "command").exists()


def test_roadmap_task_ids_are_unique() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    ids = re.findall(r"^- \[[ x]\] \*\*(P\d+-T\d+)", text, flags=re.MULTILINE)
    assert ids
    assert len(ids) == len(set(ids))
