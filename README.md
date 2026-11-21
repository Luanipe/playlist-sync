# playlist-sync

Copy playlists, liked tracks and saved albums between streaming services — initially
**Spotify** and **YouTube Music**, in both directions.

> **Status: pre-alpha (Phase 0 — repository bootstrap).**
> The project is not usable yet: the only working command is `playlist-sync --help`.
> This README is a skeleton and will grow as the roadmap phases are completed.

## What it is

A local, open-source Python application that runs on your own machine, on demand. There is no
hosted backend and no telemetry; nothing leaves your computer except calls to the streaming
services you connect.

- **Additive only** — it only adds to the destination; it never deletes anything, on either side.
- **On demand** — you start a migration when you want; there is no background sync.
- **Two steps** — `plan` previews the changes (read-only); `apply` executes them.
- **Resumable and idempotent** — re-running never duplicates tracks.
- **Automatic matching** — high-confidence matches migrate; the rest are stored as pending for
  you to review later. `apply` never prompts.
- **CLI first**, local web UI later (phase 7).

## Status

Phase 0 of the roadmap (`docs/ROADMAP.md`). Implemented so far: package bootstrap, the
`playlist-sync` console entry point (`--help` only), lint/type/test configuration, and CI.
No service adapters, matching or migration logic exist yet.

## Disclaimer

- `ytmusicapi` is unofficial and its use may conflict with YouTube's terms of service.
- Not affiliated with, endorsed by or sponsored by Spotify or Google.
- YouTube Music auth captures browser cookies, which grant account access. Cookies are stored
  **only in the operating system keyring**, never in plain text.
- Spotify uses your own Client ID with the PKCE flow; no client secret is used.
- Automated YouTube Music login may break or be restricted by Google at any time. Use at your
  own risk.

## Requirements

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/) for development

## Development

```bash
uv sync --all-extras

uv run ruff check . && uv run ruff format --check .
uv run mypy src/playlist_sync
uv run pytest -q

uv run playlist-sync --help
```

See `CONTRIBUTING.md` for the workflow and commit conventions. The design lives in `docs/`:
`PRD.md`, `ARCHITECTURE.md`, `MATCHING.md`, `AUTH.md`, `DECISIONS.md` and `ROADMAP.md`.

## License

MIT — see [`LICENSE`](LICENSE).
