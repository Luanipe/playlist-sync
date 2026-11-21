# ROADMAP

Work queue for humans and agents. Read `docs/AGENT_WORKFLOW.md` for the autonomous loop and
`AGENTS.md` for the golden rules.

**Current phase: 1**

## How agents use this file

- Work **one task per invocation**: pick the first unchecked `P<phase>-T<n>` of the current phase.
- Read the task's `Files`, `Deps` and `DoD` before coding, and the docs listed there.
- Do not start the next task. Stop at the end of the task (and summarize at the end of the phase).
- Before committing: tick the task, run the four gates, and get `reviewer` APPROVE
  (`security-audit` too when the task touches auth/secrets/network/UI/dependencies).
- If a task is ambiguous or conflicts with the docs, **stop and ask**.
- IDs are stable. Never renumber a completed task.

Legend: `[ ]` todo · `[x]` done. Task IDs: `P<phase>-T<number>`.

## Phase index

| Phase | Status | Focus |
|---|---|---|
| 0 | done | Repository bootstrap |
| 1 | active | Domain, interfaces, Singleton, Registry |
| 2 | pending | Adapters (read) and auth |
| 3 | pending | Matching |
| 4 | pending | DiffEngine and `plan` |
| 5 | pending | `apply` |
| 6 | pending | Report and pending management |
| 7 | pending | Local UI |
| 8 | pending | Open-source release |

---

## Phase 0 — Repository bootstrap

**Status:** done · **Depends on:** — · **Accept:** `uv sync`, `ruff`, `mypy`, `pytest` all run
green on an empty skeleton; CI green (CI temporarily disabled during bootstrap — see the P0-T05
note below).

- [x] **P0-T01 — Project metadata and dependencies** (`pyproject.toml`; deps: —)
  - DoD: hatchling + `src/` layout, Python ≥ 3.11, runtime deps, extras `ytmusic-login`/`ui`/`dev`; `uv sync --all-extras` resolves.
- [x] **P0-T02 — Console script** (`pyproject.toml`, `src/playlist_sync/cli.py`, `tests/unit/test_cli.py`; deps: P0-T01)
  - DoD: `playlist-sync = playlist_sync.cli:app`; `uv run playlist-sync --help` exits 0.
- [x] **P0-T03 — ruff + mypy + pytest config** (`pyproject.toml`, `tests/unit/test_tooling_config.py`; deps: P0-T01)
  - DoD: lint/format rules; `mypy --strict` override for `domain/`/`core/`; pytest testpaths.
- [x] **P0-T04 — `.gitignore`** (`.gitignore`, `tests/unit/test_gitignore.py`; deps: P0-T01)
  - DoD: venvs, caches, `*.db`, `.env`, tokens, cookies, browser profiles, reports, personal fixtures.
- [x] **P0-T05 — GitHub Actions** (`.github/workflows/ci.yml`, `tests/unit/test_ci_workflow.py`; deps: P0-T02, P0-T03)
  - DoD: lint + types + tests on Python 3.11/3.12/3.13, Linux + Windows + macOS; actions pinned by SHA.
  - Note (2026-11-21): `macos-latest` was removed from the matrix and the `CI` workflow was disabled
    in the GitHub repository settings during bootstrap. Re-enable CI (and reconsider macOS) at the
    end of Phase 1 / start of Phase 2, once there is real code to validate.
- [x] **P0-T06 — Repository docs** (`README.md`, `LICENSE`, `CONTRIBUTING.md`, `tests/unit/test_docs_skeleton.py`, `pyproject.toml`; deps: P0-T01)
  - DoD: README (what/status/disclaimer), MIT license, contributing guide.
- [x] **P0-T07 — Package skeleton** (`src/playlist_sync/**` per `docs/ARCHITECTURE.md` §2, `tests/unit/test_package_structure.py`; deps: P0-T01)
  - DoD: packages + module stubs + `py.typed`; all importable.

## Phase 1 — Domain, interfaces, Singleton, Registry

**Status:** active · **Depends on:** Phase 0 · **Accept:** contract suite green for `FakeService`;
singleton and registry fully tested; `mypy --strict` clean on `domain/`, `core/`.

- [ ] **P1-T01 — Exception hierarchy** (`src/playlist_sync/errors.py`, `tests/unit/test_errors.py`; deps: —)
  - DoD: `AuthExpiredError`, `RateLimitError`, `ServiceUnavailableError`, `TrackNotFoundError`; tested.
- [ ] **P1-T02 — Domain models** (`src/playlist_sync/domain/models.py`, `tests/unit/test_domain_models.py`; deps: P1-T01)
  - DoD: frozen `dataclass(slots=True)` `Track`, `Playlist`, `Album` per `ARCHITECTURE.md` §3; immutability tested.
- [ ] **P1-T03 — StreamingService interface** (`src/playlist_sync/services/base.py`, `tests/unit/test_services_base.py`; deps: P1-T02)
  - DoD: `StreamingService` ABC + `Capabilities` per §4; no remove/delete/unlike/unfollow methods.
- [ ] **P1-T04 — SingletonMeta** (`src/playlist_sync/core/singleton.py`, `tests/unit/test_singleton.py`; deps: —)
  - DoD: thread-safe metaclass, `reset()`, concurrency test.
- [ ] **P1-T05 — ServiceRegistry** (`src/playlist_sync/services/registry.py`, `tests/unit/test_registry.py`; deps: P1-T03, P1-T04)
  - DoD: `register`/`get`/`available`/`reset`; entry-point discovery for `playlist_sync.services`.
- [ ] **P1-T06 — FakeService** (`tests/fakes/__init__.py`, `tests/fakes/fake_service.py`; deps: P1-T03)
  - DoD: in-memory, configurable catalog, records writes, additive only.
- [ ] **P1-T07 — Contract suite** (`tests/contract/__init__.py`, `tests/contract/test_streaming_service_contract.py`; deps: P1-T06)
  - DoD: reusable, parametrized contract suite; passes for `FakeService`.
- [ ] **P1-T08 — config.py** (`src/playlist_sync/config.py`, `tests/unit/test_config.py`; deps: P1-T01)
  - DoD: pydantic settings + `config.toml`, defaults per §12; no secrets in config.
- [ ] **P1-T09 — No-destructive-methods guard** (`tests/unit/test_no_destructive_methods.py`; deps: P1-T03)
  - DoD: asserts `StreamingService` exposes no `remove*`/`delete*`/`unlike*`/`unfollow*`.

## Phase 2 — Adapters (read) and auth

**Status:** pending · **Depends on:** Phase 1 · **Accept:** real manual smoke test by the owner lists
playlists on both services; no write method exercised; no secrets in logs or repo.

- [ ] **P2-T01 — Verify Spotify/ytmusicapi APIs** (`docs/DECISIONS.md`, `docs/AUTH.md`; deps: Phase 1)
  - DoD: current API/auth behavior verified; findings logged; discrepancies raised with the human.
- [ ] **P2-T02 — TokenStore** (`src/playlist_sync/services/auth/token_store.py`, `tests/unit/test_token_store.py`; deps: P1-T01)
  - DoD: keyring `get`/`set`/`delete` + in-memory fake; no plain-text fallback.
- [ ] **P2-T03 — Spotify PKCE auth + CLI** (`services/auth/base.py`, `services/auth/spotify_pkce.py`, `cli.py`, `tests/unit/test_spotify_pkce.py`; deps: P2-T02)
  - DoD: S256 PKCE, `state` validation, loopback callback, tokens in keyring; `playlist-sync auth spotify`.
- [ ] **P2-T04 — SpotifyService (read)** (`services/spotify/adapter.py`, `tests/unit/test_spotify_service.py`; deps: P2-T03, P1-T03)
  - DoD: all read methods, full pagination, ISRC mapped.
- [ ] **P2-T05 — Spotify mapper** (`services/spotify/mapper.py`, `tests/fixtures/spotify/`, `tests/unit/test_spotify_mapper.py`; deps: P2-T04)
  - DoD: pure functions; fixture-based tests.
- [ ] **P2-T06 — YTMusicHeadersAuth** (`services/auth/ytmusic_headers.py`, `tests/unit/test_ytmusic_headers.py`; deps: P2-T02)
  - DoD: paste-headers fallback stored in keyring.
- [ ] **P2-T07 — YTMusicBrowserAuth** (`services/auth/ytmusic_browser.py`, `tests/unit/test_sapisidhash.py`, `docs/MANUAL_TESTS.md`; deps: P2-T06)
  - DoD: visible persistent context, cookie capture, SAPISIDHASH tests, manual checklist.
- [ ] **P2-T08 — YTMusicService (read + mapper)** (`services/ytmusic/adapter.py`, `services/ytmusic/mapper.py`, `tests/fixtures/ytmusic/`, `tests/unit/test_ytmusic_service.py`; deps: P2-T06)
  - DoD: read methods + search (songs first, videos fallback); mapper + fixtures.
- [ ] **P2-T09 — Error translation** (`services/spotify/adapter.py`, `services/ytmusic/adapter.py`, `tests/unit/test_error_translation.py`; deps: P2-T04, P2-T08)
  - DoD: vendor errors → project exceptions; `AuthExpiredError` on 401/403.
- [ ] **P2-T10 — Retry/rate-limit decorators** (`services/decorators.py`, `tests/unit/test_decorators.py`; deps: P1-T01)
  - DoD: `with_retry` (backoff/jitter/`Retry-After`) and `rate_limited` per `ARCHITECTURE.md` §6.
- [ ] **P2-T11 — Contract suite for adapters** (`tests/contract/**`, `tests/fixtures/**`; deps: P2-T04, P2-T08, P2-T09)
  - DoD: green for both adapters against recorded fixtures.
- [ ] **P2-T12 — CLI playlists** (`cli.py`, `tests/unit/test_cli_playlists.py`; deps: P2-T04, P2-T08)
  - DoD: `playlist-sync playlists --service spotify|ytmusic`, read-only.

## Phase 3 — Matching

**Status:** pending · **Depends on:** Phase 2 · **Accept:** quality gate passes (0 wrong-version
auto-matches in the trap group, ≥ 90% overall).

- [ ] **P3-T01 — Normalization** (`core/normalize.py`, `tests/unit/test_normalize.py`; deps: P1-T01)
  - DoD: NFKD, accents, casefold, punctuation, whitespace, feat credits, artist sets (`MATCHING.md` §1).
- [ ] **P3-T02 — Version markers** (`core/normalize.py`, `tests/unit/test_version_markers.py`; deps: P3-T01)
  - DoD: marker extraction incl. multilingual basics (`MATCHING.md` §2).
- [ ] **P3-T03 — Strategies, scorer, vetoes, decision** (`core/matching/strategies.py`, `core/matching/scorer.py`, `core/matching/matcher.py`, `tests/unit/test_matching_*.py`; deps: P3-T02)
  - DoD: strategies, weights, vetoes, decision and tiebreakers per `MATCHING.md` §3–§6.
- [ ] **P3-T04 — Matching fixtures + quality gate** (`tests/fixtures/matching_cases.json`, `tests/unit/test_matching_quality.py`; deps: P3-T03)
  - DoD: ≥ 100 labeled cases (anonymized); 0 wrong-version traps; ≥ 90% overall.
- [ ] **P3-T05 — Repository + SQLite + migrations** (`storage/repository.py`, `storage/sqlite_repo.py`, `storage/schema.sql`, `tests/unit/test_repository.py`; deps: P1-T01)
  - DoD: `track_matches`/`unmatched` tables; migrations via `PRAGMA user_version`.
- [ ] **P3-T06 — Destination query builders** (`core/matching/queries.py`, `tests/unit/test_query_builders.py`; deps: P3-T03, P3-T05)
  - DoD: ISRC first for Spotify; text query for YouTube Music (`MATCHING.md` §7).

## Phase 4 — DiffEngine and `plan`

**Status:** pending · **Depends on:** Phase 3 · **Accept:** integration tests with two
`FakeService`s, both directions; `plan` performs zero writes.

- [ ] **P4-T01 — PlaylistLinker + `playlist_links`** (`core/linker.py`, `storage/sqlite_repo.py`, `tests/unit/test_linker.py`; deps: P3-T05)
  - DoD: link table → exact normalized name → create; deterministic (`ARCHITECTURE.md` §9).
- [ ] **P4-T02 — DiffEngine** (`core/diff.py`, `tests/unit/test_diff.py`; deps: P4-T01, P3-T03, P3-T05)
  - DoD: three layers, duplicates and manual additions (`ARCHITECTURE.md` §8).
- [ ] **P4-T03 — MigrationPlan + Actions + JSON** (`core/plan.py`, `tests/unit/test_plan.py`; deps: P4-T02)
  - DoD: action types, ordered plan, JSON round-trip.
- [ ] **P4-T04 — MigrationService.plan (read-only)** (`core/migration.py`, `tests/unit/test_migration_plan.py`; deps: P4-T03)
  - DoD: builds a plan without writes; test asserts zero write calls.
- [ ] **P4-T05 — CLI plan** (`cli.py`, `tests/unit/test_cli_plan.py`; deps: P4-T04)
  - DoD: `playlist-sync plan --from X --to Y [--save plan.json]` with to-migrate/pending/extras summary.
- [ ] **P4-T06 — Liked tracks and saved albums as sources** (`core/migration.py`, `core/plan.py`, `tests/unit/test_special_sources.py`; deps: P4-T04)
  - DoD: `liked` and `saved_albums` modeled as special playlists.

## Phase 5 — `apply`

**Status:** pending · **Depends on:** Phase 4 · **Accept:** re-run performs zero writes; interrupted
run resumes; A→B then B→A yields the union with no duplicates; owner manual test.

- [ ] **P5-T01 — Executable actions** (`core/plan.py`, `tests/unit/test_actions.py`; deps: P4-T03)
  - DoD: `CreatePlaylist`, `AddTracks`, `LikeTracks`, `SaveAlbums`.
- [ ] **P5-T02 — Adapter write methods** (`services/spotify/adapter.py`, `services/ytmusic/adapter.py`, `tests/unit/test_adapter_writes.py`; deps: P5-T01, P2-T04, P2-T08)
  - DoD: additive only; batching within vendor limits.
- [ ] **P5-T03 — Idempotent, resumable apply** (`core/migration.py`, `storage/sqlite_repo.py`, `tests/integration/test_apply_resume.py`; deps: P5-T01, P5-T02)
  - DoD: progress in `runs`; re-run performs zero writes; interrupted run resumes.
- [ ] **P5-T04 — Persist matches and unmatched reasons** (`core/migration.py`, `storage/sqlite_repo.py`, `tests/unit/test_persistence.py`; deps: P5-T03)
  - DoD: automatic matches (`manual = false`, score) and unmatched reasons persisted.
- [ ] **P5-T05 — Per-action error handling** (`core/migration.py`, `tests/integration/test_apply_errors.py`; deps: P5-T03)
  - DoD: one failure does not abort the run; recorded as `error` in `unmatched`.
- [ ] **P5-T06 — CLI apply** (`cli.py`, `tests/unit/test_cli_apply.py`; deps: P5-T03)
  - DoD: `playlist-sync apply`.

## Phase 6 — Report and pending management

**Status:** pending · **Depends on:** Phase 5 · **Accept:** report snapshot tests; resolving a
pending item makes the next run migrate it.

- [ ] **P6-T01 — End-of-run report** (`reporting/summary.py`, `tests/unit/test_report.py`; deps: Phase 5)
  - DoD: three blocks; `--show-extras`.
- [ ] **P6-T02 — CSV/JSON export** (`reporting/export.py`, `tests/unit/test_export.py`; deps: P6-T01)
  - DoD: export to the reports dir.
- [ ] **P6-T03 — `unmatched list|resolve|ignore`** (`cli.py`, `storage/sqlite_repo.py`, `tests/unit/test_cli_unmatched.py`; deps: P5-T04)
  - DoD: paste link/id; ignore forever.
- [ ] **P6-T04 — Retry policy** (`core/migration.py`, `storage/sqlite_repo.py`, `tests/unit/test_retry_policy.py`; deps: P6-T03)
  - DoD: `retry_not_found_days`, `--retry-unmatched`; reasons per `ARCHITECTURE.md` §8.
- [ ] **P6-T05 — `fix` command** (`cli.py`, `core/migration.py`, `tests/unit/test_cli_fix.py`; deps: P6-T03)
  - DoD: replace a wrong automatic match.
- [ ] **P6-T06 — Album matching (ADR + implementation)** (`docs/DECISIONS.md`, `core/matching/*`, `tests/unit/test_album_matching.py`; deps: Phase 5)
  - DoD: ADR accepted; album search/resolution implemented and tested.

## Phase 7 — Local UI

**Status:** pending · **Depends on:** Phase 6 · **Accept:** owner completes a full migration using
only the UI.

- [ ] **P7-T01 — ADR: choose the UI framework** (`docs/DECISIONS.md`; deps: Phase 6)
  - DoD: FastAPI+HTMX vs NiceGUI decided and recorded.
- [ ] **P7-T02 — First-run wizard** (`ui/**`, `tests/unit/test_ui_wizard.py`; deps: P7-T01)
  - DoD: Spotify app creation guide, Client ID, redirect URI.
- [ ] **P7-T03 — Connect buttons + reconnect** (`ui/**`, `tests/unit/test_ui_connect.py`; deps: P7-T02)
  - DoD: status badges; reconnect on `AuthExpiredError`.
- [ ] **P7-T04 — Direction, playlists, Plan, Apply, report** (`ui/**`, `tests/unit/test_ui_flow.py`; deps: P7-T03)
  - DoD: full flow in the UI using the same core.
- [ ] **P7-T05 — `playlist-sync ui`** (`cli.py`, `ui/**`, `tests/unit/test_cli_ui.py`; deps: P7-T04)
  - DoD: opens the browser at `127.0.0.1`.
- [ ] **P7-T06 — Loopback + CSRF** (`ui/**`, `tests/unit/test_ui_security.py`; deps: P7-T05)
  - DoD: UI binds to loopback only; CSRF protection on state-changing endpoints.

## Phase 8 — Open-source release

**Status:** pending · **Depends on:** Phase 7 · **Accept:** fresh machine install works from the
README alone.

- [ ] **P8-T01 — Plugin documentation** (`CONTRIBUTING.md`, `docs/PLUGINS.md`; deps: Phase 7)
  - DoD: "how to write an adapter", entry-point example, contract-test how-to.
- [ ] **P8-T02 — Final README** (`README.md`; deps: P8-T01)
  - DoD: `pipx` install, screenshots, disclaimers, privacy statement, FAQ, troubleshooting.
- [ ] **P8-T03 — Community files** (`.github/**`, `SECURITY.md`, `CODE_OF_CONDUCT.md`; deps: —)
  - DoD: issue/PR templates, security policy, code of conduct.
- [ ] **P8-T04 — PyInstaller builds (optional)** (`.github/workflows/release.yml`, `packaging/**`; deps: P8-T02)
  - DoD: builds published in GitHub Releases.
- [ ] **P8-T05 — PyPI publish + versioning** (`.github/workflows/publish.yml`, `CHANGELOG.md`, `pyproject.toml`; deps: P8-T02)
  - DoD: publish workflow, versioning and changelog.
- [ ] **P8-T06 — Final license** (`LICENSE`, `docs/DECISIONS.md`; deps: —)
  - DoD: final license text applied (MIT per ADR-014) and metadata confirmed.
