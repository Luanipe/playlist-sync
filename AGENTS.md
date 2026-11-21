# AGENTS.md — playlist-sync

Local, open-source Python app that copies playlists, liked tracks and saved albums
between streaming services (initially **Spotify** and **YouTube Music**, both directions).
Runs on the user's machine, on demand. No hosted backend, no telemetry.

You are the primary developer of this project. Read this file fully before every task.

## Source of truth (read before coding)

| Document | Purpose |
|---|---|
| `docs/PRD.md` | What we build and why, scope and non-goals |
| `docs/ARCHITECTURE.md` | Layers, patterns, interfaces, DB schema, folder layout |
| `docs/MATCHING.md` | Track matching algorithm, scoring, veto rules, thresholds |
| `docs/AUTH.md` | Spotify PKCE and YouTube Music (Playwright) login |
| `docs/DECISIONS.md` | Decisions already made (ADR log). Do not re-litigate them |
| `docs/ROADMAP.md` | Phases, tasks, acceptance criteria. Your work queue |
| `docs/AGENT_WORKFLOW.md` | Autonomous agent loop: roles, gates, commit policy, escalation |

If code and docs disagree, **stop and ask**; do not silently pick one.
If you must make a new design decision, add an entry to `docs/DECISIONS.md` in the same PR.

## Golden rules (invariants — never violate)

1. **Additive only. The program never deletes anything on any service.**
   `StreamingService` has NO remove/delete methods, and you must not add any.
2. **The core never imports service SDKs.** `domain/`, `core/`, `storage/`, `reporting/`
   must not import `spotipy`, `ytmusicapi`, `playwright` or any vendor library.
   Only `services/<name>/` may.
3. **Dependency injection into the core.** `MigrationService`, `DiffEngine`, etc. receive
   `StreamingService` instances as parameters. Singletons are resolved only at the
   composition root (CLI/UI entry points) through `ServiceRegistry`.
4. **`plan` is read-only.** Only `apply` may call write methods on adapters.
5. **No secrets in the repo or in plain-text files.** Tokens and cookies go to `keyring`.
   The SQLite DB and config live in user directories via `platformdirs`.
6. **Tests never touch the network.** Use `FakeService` and recorded fixtures.
7. **No telemetry, no analytics, no outbound calls** other than to the streaming services.
8. **Automatic mode.** `apply` never prompts. Low-confidence matches go to `unmatched`.

## Tech stack

- Python **3.11+**, `src/` layout, package name `playlist_sync`
- Packaging: `pyproject.toml` (hatchling). Dev env: `uv`
- Libs: `spotipy`, `ytmusicapi`, `rapidfuzz`, `typer`, `platformdirs`, `keyring`,
  `tenacity` (retry), `pydantic` (config), `rich` (CLI output)
- Optional extra `ytmusic-login`: `playwright`
- UI (phase 7): `FastAPI` + simple HTML/HTMX, or `NiceGUI` (decide in an ADR first)
- Quality: `ruff` (lint + format), `mypy --strict` on `domain/` and `core/`, `pytest`, `pytest-cov`

Before using any library API, **check its current documentation or installed version**.
Do not rely on memory for `spotipy`, `ytmusicapi`, Spotify Web API rules or Playwright.

## Commands

```bash
uv sync --all-extras          # install
uv run ruff check . && uv run ruff format --check .
uv run mypy src/playlist_sync
uv run pytest -q              # must pass offline
uv run playlist-sync --help   # CLI entry point
```

All of lint, types and tests must pass before you consider a task done.

## Conventions

- Code, comments, docstrings, commit messages, docs: **English**.
- Type hints everywhere. Domain models are frozen `dataclass(slots=True)`.
- Small modules, small functions. No god classes. Prefer composition over inheritance.
- Errors: raise the project exceptions in `playlist_sync/errors.py`
  (`AuthExpiredError`, `RateLimitError`, `ServiceUnavailableError`, `TrackNotFoundError`).
  Adapters translate vendor exceptions into these. Never leak vendor exceptions to the core.
- Logging with `logging` (no `print` outside the CLI/UI layer). Never log tokens, cookies or headers.
- Commits: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`).
- One phase at a time. One focused change per commit.

## How to work

Follow `docs/AGENT_WORKFLOW.md` for the full autonomous loop.

1. Open `docs/ROADMAP.md`, find the first unchecked task of the current phase (stable ID
   `P<phase>-T<n>`).
2. Read the docs relevant to it. Restate the plan briefly before large changes.
3. Write tests first or together with the code. Every new behavior has a test.
4. Run lint, types and tests. Fix everything.
5. Tick the task in `docs/ROADMAP.md` and note anything deferred.
6. Commit locally with a Conventional Commit that includes the task ID
   (e.g. `feat(P1-T03): ...`). Never push.
7. Stop at the end of each task; stop and summarize at the end of each phase.

**Ask the human instead of guessing** when: a doc is ambiguous, an external API behaves
differently from the docs, a decision would change a golden rule, or a task needs credentials.

## Do NOT

- Add delete/remove/unfollow operations, even "just for tests" on real adapters.
- Add features outside the current phase or listed in "Non-goals" of `docs/PRD.md`.
- Commit `.env`, tokens, cookies, `*.db`, recorded fixtures with personal data.
- Hardcode a Client ID, secret or user data.
- Swallow exceptions silently or catch bare `Exception` without re-raising or logging.
- Rewrite the architecture without an ADR approved by the human.

## Definition of done (per task)

- [ ] Behavior implemented as described in the docs
- [ ] Tests added and passing offline
- [ ] `ruff`, `mypy`, `pytest` green
- [ ] No golden rule violated
- [ ] Docs/ROADMAP updated; new decisions logged in `DECISIONS.md`
