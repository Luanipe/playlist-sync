"""Tests for the CLI entry point (console script)."""

from __future__ import annotations

from importlib.metadata import entry_points

from typer.testing import CliRunner

from playlist_sync.cli import app

runner = CliRunner()


def test_console_script_entry_point_is_registered() -> None:
    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts.get("playlist-sync") == "playlist_sync.cli:app"


def test_help_exits_successfully() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
