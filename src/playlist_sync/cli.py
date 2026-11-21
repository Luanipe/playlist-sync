"""Command-line interface for playlist-sync.

This module is the composition root for the CLI. Subcommands and
``ServiceRegistry`` wiring are added in later phases; for now it only exposes the
``app`` object referenced by the ``playlist-sync`` console script.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="playlist-sync",
    help="Copy playlists, liked tracks and saved albums between streaming services.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Copy playlists, liked tracks and saved albums between streaming services."""
