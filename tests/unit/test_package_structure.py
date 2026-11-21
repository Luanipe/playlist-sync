"""Tests that the package skeleton follows docs/ARCHITECTURE.md §2."""

from __future__ import annotations

import importlib
from pathlib import Path

import playlist_sync

PACKAGE_ROOT = Path(playlist_sync.__file__).resolve().parent

# Package directories from §2 (relative to the top-level package).
EXPECTED_PACKAGES = [
    "",
    "domain",
    "core",
    "core/matching",
    "services",
    "services/auth",
    "services/spotify",
    "services/ytmusic",
    "storage",
    "reporting",
    "ui",
]

# Modules from §2, plus the CLI that already existed.
EXPECTED_MODULES = [
    "playlist_sync.errors",
    "playlist_sync.config",
    "playlist_sync.domain.models",
    "playlist_sync.services.base",
    "playlist_sync.services.registry",
    "playlist_sync.services.decorators",
    "playlist_sync.services.auth.base",
    "playlist_sync.services.auth.spotify_pkce",
    "playlist_sync.services.auth.ytmusic_browser",
    "playlist_sync.services.auth.ytmusic_headers",
    "playlist_sync.services.auth.token_store",
    "playlist_sync.services.spotify.adapter",
    "playlist_sync.services.spotify.mapper",
    "playlist_sync.services.ytmusic.adapter",
    "playlist_sync.services.ytmusic.mapper",
    "playlist_sync.core.singleton",
    "playlist_sync.core.normalize",
    "playlist_sync.core.matching.strategies",
    "playlist_sync.core.matching.scorer",
    "playlist_sync.core.matching.matcher",
    "playlist_sync.core.diff",
    "playlist_sync.core.plan",
    "playlist_sync.core.linker",
    "playlist_sync.core.migration",
    "playlist_sync.storage.repository",
    "playlist_sync.storage.sqlite_repo",
    "playlist_sync.reporting.summary",
    "playlist_sync.reporting.export",
    "playlist_sync.cli",
]


def test_package_dirs_have_init() -> None:
    for package in EXPECTED_PACKAGES:
        assert (PACKAGE_ROOT / package / "__init__.py").is_file(), package


def test_all_modules_are_importable() -> None:
    for module in EXPECTED_MODULES:
        importlib.import_module(module)


def test_non_python_skeleton_files_exist() -> None:
    assert (PACKAGE_ROOT / "py.typed").is_file()
    assert (PACKAGE_ROOT / "storage" / "schema.sql").is_file()
