"""Smoke tests for the package skeleton."""

import playlist_sync


def test_package_is_importable() -> None:
    assert playlist_sync.__name__ == "playlist_sync"
