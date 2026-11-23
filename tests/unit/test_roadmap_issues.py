"""Tests for the roadmap -> GitHub issues helper (offline; no `gh` calls)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script() -> ModuleType:
    path = ROOT / "scripts" / "sync_roadmap_issues.py"
    spec = importlib.util.spec_from_file_location("sync_roadmap_issues", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sync = _load_script()

SAMPLE = """# ROADMAP

## Phase 1 — Test phase

- [x] **P1-T01 — Done thing** (`a.py`; deps: —)
  - DoD: done.
- [ ] **P1-T02 — Pending thing** (`b.py`, `c.py`; deps: P1-T01)
  - DoD: works.
    with more detail.
  - Note: careful.

## Phase 2 — Next phase

- [ ] **P2-T01 — Other thing** (`d.py`; deps: Phase 1)
  - DoD: other.
"""


def test_parse_roadmap_extracts_fields_and_details() -> None:
    tasks = sync.parse_roadmap(SAMPLE)

    assert [task.id for task in tasks] == ["P1-T01", "P1-T02", "P2-T01"]
    done, pending, other = tasks

    assert done.done is True
    assert done.phase == 1
    assert done.files == "`a.py`"
    assert done.deps == "—"

    assert pending.title == "Pending thing"
    assert pending.files == "`b.py`, `c.py`"
    assert pending.deps == "P1-T01"
    assert pending.phase_title == "Test phase"
    assert pending.details == ["DoD: works. with more detail.", "Note: careful."]

    assert other.phase == 2
    assert other.deps == "Phase 1"


def test_issue_body_contains_task_contract() -> None:
    task = sync.parse_roadmap(SAMPLE)[1]

    body = sync.issue_body(task, "https://github.com/owner/repo")

    assert "playlist-sync-roadmap-task: P1-T02" in body
    assert "## P1-T02 — Pending thing" in body
    assert "**Phase:** 1 — Test phase" in body
    assert "**Depends on:** P1-T01" in body
    assert "https://github.com/owner/repo/blob/main/docs/ROADMAP.md" in body
    assert "- DoD: works. with more detail." in body
    assert "source of truth" in body


def test_render_issues_doc_links_existing_issues() -> None:
    tasks = sync.parse_roadmap(SAMPLE)

    doc = sync.render_issues_doc(tasks, {"P1-T02": 12}, "https://github.com/owner/repo")

    assert "`P1-T02` — Pending thing | 1 | todo | [#12]" in doc
    assert "`P1-T01` — Done thing | 1 | done | —" in doc
    assert "Do not edit by hand" in doc


def test_parse_repo_slug_accepts_https_ssh_and_dots() -> None:
    assert sync.parse_repo_slug("https://github.com/owner/playlist-sync.git") == (
        "owner/playlist-sync"
    )
    assert sync.parse_repo_slug("git@github.com:owner/playlist-sync.git") == ("owner/playlist-sync")
    assert sync.parse_repo_slug("https://github.com/owner/my.repo.git") == "owner/my.repo"


def test_resolve_repo_slug_refuses_foreign_repo() -> None:
    origin = "https://github.com/owner/playlist-sync.git"
    assert sync.resolve_repo_slug(origin, None) == "owner/playlist-sync"
    assert sync.resolve_repo_slug(origin, "owner/playlist-sync") == "owner/playlist-sync"

    with pytest.raises(ValueError, match="does not match origin"):
        sync.resolve_repo_slug(origin, "victim/repo")

    assert sync.resolve_repo_slug(origin, "victim/repo", allow_foreign=True) == "victim/repo"


def test_parse_roadmap_rejects_malformed_task_lines() -> None:
    with pytest.raises(ValueError, match="malformed roadmap task line"):
        sync.parse_roadmap("- [ ] **P1-T02 broken task line**\n")


def _issue(number: int, title: str, body: str = "") -> dict[str, object]:
    return {
        "number": number,
        "title": title,
        "state": "OPEN",
        "url": f"https://github.com/owner/repo/issues/{number}",
        "body": body,
    }


def test_sync_issues_is_idempotent_and_uses_the_stable_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tasks = sync.parse_roadmap(SAMPLE)
    existing = [
        _issue(12, "Renamed upstream title", "<!-- playlist-sync-roadmap-task: P1-T02 -->"),
    ]
    calls: list[tuple[str, ...]] = []

    def fake_run_gh(*args: str) -> str:
        calls.append(args)
        if args[:2] == ("issue", "list"):
            return json.dumps(existing)
        raise AssertionError(f"unexpected gh call: {args}")

    monkeypatch.setattr(sync, "run_gh", fake_run_gh)

    numbers = sync.sync_issues(
        tasks,
        "owner/repo",
        "https://github.com/owner/repo",
        update=False,
        phase_filter=1,
    )

    assert numbers["P1-T02"] == 12
    assert not any(call[:2] == ("issue", "create") for call in calls)


def test_sync_update_never_closes_or_deletes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tasks = sync.parse_roadmap(SAMPLE)
    existing = [
        _issue(12, "Pending thing", "<!-- playlist-sync-roadmap-task: P1-T02 -->"),
    ]
    calls: list[tuple[str, ...]] = []

    def fake_run_gh(*args: str) -> str:
        calls.append(args)
        if args[:2] == ("issue", "list"):
            return json.dumps(existing)
        if args[:2] == ("issue", "edit"):
            return ""
        raise AssertionError(f"unexpected gh call: {args}")

    monkeypatch.setattr(sync, "run_gh", fake_run_gh)

    sync.sync_issues(
        tasks,
        "owner/repo",
        "https://github.com/owner/repo",
        update=True,
        phase_filter=1,
    )

    assert any(call[:3] == ("issue", "edit", "12") for call in calls)
    assert not any(call[:2] in {("issue", "close"), ("issue", "delete")} for call in calls)


def test_real_roadmap_and_issue_mapping_are_consistent() -> None:
    tasks = sync.parse_roadmap((ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8"))
    mapping = (ROOT / "docs" / "ISSUES.md").read_text(encoding="utf-8")

    ids = [task.id for task in tasks]
    assert len(ids) == len(set(ids))
    assert all(task.phase >= 0 for task in tasks)
    assert any(task.id == "P1-T02" and not task.done for task in tasks)
    assert any(task.done for task in tasks)

    rows = {
        line.split("|")[1].strip(): line for line in mapping.splitlines() if line.startswith("|")
    }
    for task in tasks:
        row = next(line for key, line in rows.items() if f"`{task.id}`" in key)
        expected = "done" if task.done else "todo"
        assert f"| {expected} |" in row, (task.id, row)
