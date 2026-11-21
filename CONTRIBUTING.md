# Contributing to playlist-sync

This is a small, solo-maintained open-source project. Keep changes small, focused and
consistent with the existing code. All code, comments, docstrings and docs are written in
English.

## Before you start

1. Read [`AGENTS.md`](AGENTS.md) — it lists the golden rules that must never be violated.
2. Read the design docs in [`docs/`](docs/): `PRD.md`, `ARCHITECTURE.md`, `MATCHING.md`,
   `AUTH.md`, `DECISIONS.md` and `ROADMAP.md`.
3. Work one roadmap phase at a time, and make one focused change per commit.

Golden rules (summary): additive only — never delete; the core never imports service SDKs;
dependency injection into the core; `plan` is read-only; no secrets in the repo; tests never
touch the network; no telemetry; `apply` never prompts.

## Development setup

```bash
uv sync --all-extras
```

The YouTube Music browser login uses the optional `ytmusic-login` extra (Playwright).

## Quality gates

All of these must pass before a change is considered done:

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/playlist_sync
uv run pytest -q
```

Additional expectations:

- Type hints everywhere; `domain/` and `core/` are checked with `mypy --strict`.
- Tests never touch the network — use `FakeService` and recorded fixtures.
- Never log tokens, cookies or headers.
- Prefer small modules and small functions; no god classes.

## Commit conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<optional scope>): <description>
```

| Type | Use for |
|---|---|
| `feat` | a new feature |
| `fix` | a bug fix |
| `test` | adding or fixing tests |
| `docs` | documentation only |
| `refactor` | a change that neither fixes a bug nor adds a feature |
| `perf` | a performance improvement |
| `chore` | build, tooling, dependencies, CI |

Rules:

- Write the description in English, in the imperative mood, with no trailing period
  (`add playlist diffing`, not `Added playlist diffing.`).
- Keep the subject line short (about 72 characters or fewer).
- One logical change per commit.
- Mention the roadmap phase or task in the body when it helps the reader.
- Never commit secrets, tokens, cookies, `*.db` files, or recorded fixtures containing
  personal data (see `.gitignore`).

## Pull requests

- Branch off `main` and keep `main` releasable.
- CI (`.github/workflows/ci.yml`) must be green on Python 3.11–3.13, on Linux, Windows and
  macOS.
- The pull-request checklist mirrors the definition of done in `AGENTS.md`.
- Do not force-push shared branches or rewrite published history.

## Adding a service adapter

Adapters live in `src/playlist_sync/services/<name>/`, register through the entry-point group
`playlist_sync.services`, and must pass the shared contract suite in `tests/contract/`. A full
"how to write an adapter" guide is planned for phase 8.

## License

By contributing, you agree that your contributions are released under the
[MIT license](LICENSE).
