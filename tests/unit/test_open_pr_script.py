"""Offline tests for scripts/open_pr.sh using a temporary local git remote."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "open_pr.sh"
BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(BASH is None, reason="bash is required")


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _commit(cwd: Path, message: str) -> None:
    _git(
        cwd,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        message,
    )


def _repo(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "--bare")

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _commit(repo, "init")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-u", "origin", "main")
    return repo


def _branch_with_commit(repo: Path, branch: str) -> None:
    _git(repo, "switch", "-c", branch)
    (repo / "work.txt").write_text(f"{branch}\n", encoding="utf-8")
    _git(repo, "add", "work.txt")
    _commit(repo, "work")


def _body(tmp_path: Path, text: str = "Closes #1\n") -> Path:
    path = tmp_path / "body.md"
    path.write_text(text, encoding="utf-8")
    return path


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    assert BASH is not None
    return subprocess.run(
        [BASH, str(SCRIPT), *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )


def test_valid_task_branch_dry_run(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _branch_with_commit(repo, "task/P1-T02-domain-models")
    body = _body(tmp_path)

    result = _run(
        repo,
        "--title",
        "feat(P1-T02): add domain models",
        "--body-file",
        str(body),
        "--issue",
        "1",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert "dry run: would push task/P1-T02-domain-models" in result.stdout


def test_relative_body_file_is_resolved_from_the_caller_cwd(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _branch_with_commit(repo, "task/P1-T02-domain-models")
    _body(tmp_path)

    result = _run(
        repo,
        "--title",
        "feat(P1-T02): add domain models",
        "--body-file",
        "../body.md",
        "--issue",
        "1",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert "dry run: would push" in result.stdout


def test_refuses_main_and_unrelated_branch(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    body = _body(tmp_path)

    on_main = _run(
        repo,
        "--title",
        "chore: workflow",
        "--body-file",
        str(body),
        "--issue",
        "1",
        "--dry-run",
    )
    assert on_main.returncode != 0
    assert "refusing to open a PR from main" in on_main.stderr

    _branch_with_commit(repo, "feature/not-allowed")
    wrong_branch = _run(
        repo,
        "--title",
        "chore: workflow",
        "--body-file",
        str(body),
        "--issue",
        "1",
        "--dry-run",
    )
    assert wrong_branch.returncode != 0
    assert "branch must be" in wrong_branch.stderr


def test_task_branch_requires_issue_and_closes_line(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _branch_with_commit(repo, "task/P1-T02-domain-models")

    missing_issue = _run(
        repo,
        "--title",
        "feat(P1-T02): add domain models",
        "--body-file",
        str(_body(tmp_path)),
        "--dry-run",
    )
    assert missing_issue.returncode != 0
    assert "task branches require --issue" in missing_issue.stderr

    missing_closes = _run(
        repo,
        "--title",
        "feat(P1-T02): add domain models",
        "--body-file",
        str(_body(tmp_path, "no issue link\n")),
        "--issue",
        "1",
        "--dry-run",
    )
    assert missing_closes.returncode != 0
    assert "must contain 'Closes #1'" in missing_closes.stderr


def test_title_base_and_clean_tree_are_validated(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _branch_with_commit(repo, "task/P1-T02-domain-models")
    body = _body(tmp_path)

    bad_title = _run(
        repo,
        "--title",
        "feat: not a task title",
        "--body-file",
        str(body),
        "--issue",
        "1",
        "--dry-run",
    )
    assert bad_title.returncode != 0
    assert "title must look like" in bad_title.stderr

    bad_base = _run(
        repo,
        "--title",
        "feat(P1-T02): add domain models",
        "--body-file",
        str(body),
        "--issue",
        "1",
        "--base",
        "develop",
        "--dry-run",
    )
    assert bad_base.returncode != 0
    assert "only supports main" in bad_base.stderr

    (repo / "README.md").write_text("dirty\n", encoding="utf-8")
    dirty = _run(
        repo,
        "--title",
        "feat(P1-T02): add domain models",
        "--body-file",
        str(body),
        "--issue",
        "1",
        "--dry-run",
    )
    assert dirty.returncode != 0
    assert "working tree is not clean" in dirty.stderr
