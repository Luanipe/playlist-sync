# DECISIONS (ADR log)

Decisions already made by the project owner. Do not change them without explicit approval.
Add new entries at the bottom using the template at the end.

---

### ADR-001 — Local app, not a hosted service
**Status:** accepted
Runs on the user's machine; no backend, no telemetry. Avoids hosting costs, privacy issues and
Spotify/Google app-approval requirements. Open source on GitHub.

### ADR-002 — Both directions from day one
**Status:** accepted
Spotify ↔ YouTube Music. The core is direction-agnostic; matching is symmetric.

### ADR-003 — On-demand execution, diff-based
**Status:** accepted
No continuous sync. Each run compares source and destination and acts only on differences.

### ADR-004 — Additive only; never delete
**Status:** accepted
`StreamingService` has no remove/delete methods. Tracks only in the destination are reported as
informational extras. Running A→B then B→A converges to the union.

### ADR-005 — Two-step `plan` → `apply`
**Status:** accepted
`plan` is read-only and serializable. `apply` executes mutating actions (Command pattern).

### ADR-006 — Automatic matching with threshold
**Status:** accepted
Score ≥ 85 migrates automatically; lower scores become pending in `unmatched`. No prompts during
`apply`. Pending items are resolved later via `playlist-sync unmatched`. Veto rules (duration,
version markers) apply regardless of score. See `docs/MATCHING.md`.

### ADR-007 — Patterns
**Status:** accepted
Adapter (services), Singleton via metaclass + Registry (one instance per service), Strategy
(matching, auth providers), Repository (SQLite), Command (plan actions), Decorator (retry/rate limit).
Singleton is used only at the composition root; the core receives services by dependency injection.
Registry exposes `reset()` for tests.

### ADR-008 — Plugins via entry points
**Status:** accepted
Third-party adapters register in entry-point group `playlist_sync.services`. A reusable contract
test suite validates any adapter.

### ADR-009 — Spotify auth: PKCE with user-provided Client ID
**Status:** accepted
Each user registers their own Spotify app (avoids shared quota limits of dev-mode apps). No client
secret. Tokens in `keyring`.

### ADR-010 — YouTube Music auth: Playwright browser login (default)
**Status:** accepted
Visible persistent browser context, capture cookies, build headers for `ytmusicapi`. Installed as
optional extra `ytmusic-login`, Chromium downloaded on demand. "Paste headers" kept as fallback
`AuthProvider`.

### ADR-011 — Storage
**Status:** accepted
SQLite behind a Repository, in the user data directory (`platformdirs`). Secrets only in `keyring`.

### ADR-012 — Interface order
**Status:** accepted
CLI first (phases 1–6); local web UI in phase 7 using the same core. UI framework choice
(FastAPI+HTMX vs NiceGUI) to be proposed via ADR at the start of phase 7.

### ADR-013 — Language and tooling
**Status:** accepted
Python 3.11+, `src/` layout, `uv`, `ruff`, `mypy`, `pytest`. All code and docs in English.

### ADR-014 — MIT license
**Status:** accepted
The project is released under the MIT license (see `LICENSE`); the SPDX identifier is declared
in `pyproject.toml`. Chosen for simplicity and permissiveness. Unlike Apache-2.0 it has no
explicit patent grant, which is acceptable for this project.

### ADR-015 — AI-driven development workflow
**Status:** accepted (push policy amended by ADR-016)
Development is driven by autonomous OpenCode agents following `docs/AGENT_WORKFLOW.md`. Work is
one roadmap task per invocation; every task must pass the quality gates and a read-only `reviewer`
(plus `security-audit` when it touches auth, secrets, network, UI or dependencies) before a
Conventional Commit. Roadmap task IDs are stable (`P<phase>-T<number>`).

### ADR-016 — Issue-driven workflow with human-reviewed PRs
**Status:** accepted
Every **pending** `docs/ROADMAP.md` task is mirrored 1:1 as a GitHub issue
(`scripts/sync_roadmap_issues.py`, mapping in `docs/ISSUES.md`). Agents implement each task on a
dedicated branch, tick the roadmap, commit and open a PR against `main` through
`scripts/open_pr.sh`, which validates the branch, title and body and never force-pushes. Agents
never push to `main` and never merge or close a PR; the owner performs the human review and the
merge. The PR links its issue with `Closes #<number>`, so the issue closes automatically on merge.

`opencode.json` denies direct `git push`, PR merges/closes, issue deletions and raw `gh api`, and
denies editing the policy, the scripts and the OpenCode definitions. It is a **local guardrail, not
a security boundary**: shell tooling can execute code, so the real boundary is GitHub branch
protection on `main` (require a PR and review, block direct pushes and force-pushes) plus the human
review. This replaces the "local commits only / never push" part of ADR-015.

---

## Open questions (agent: raise these when you reach them)

- Album migration across services: match by album search or via tracks? (phase 6)
- Handling of Spotify "local files" and unavailable/region-locked tracks
- Whether `spotipy` is kept or PKCE is implemented directly (phase 2)
- Final project/PyPI name (the package is `playlist_sync`, the distribution `playlist-sync`)

## Template

```
### ADR-NNN — Title
**Status:** proposed | accepted | superseded by ADR-XXX
Context, decision, consequences, alternatives considered.
```
