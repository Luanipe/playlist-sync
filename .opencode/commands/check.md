---
description: Run lint, format, type checks and tests
---
Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/playlist_sync && uv run pytest -q`.

Summarize failures and fix them if they are straightforward; otherwise explain what is wrong.
