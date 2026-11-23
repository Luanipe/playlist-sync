<!-- Keep this PR to one roadmap task (or one focused chore). The human owner reviews and merges. -->

## Summary

<!-- What changed and why. Link the design docs or ADR when relevant. -->

## Roadmap / issue

- Task: <!-- P1-T03, or "n/a" for a chore -->
- Phase: <!-- 1..8, or "n/a" -->
- Closes #
- Roadmap: `docs/ROADMAP.md`

## Type of change

- [ ] `feat` — new behavior
- [ ] `fix` — bug fix
- [ ] `test` — tests only
- [ ] `docs` — documentation only
- [ ] `refactor` — no behavior change
- [ ] `perf` — performance
- [ ] `chore` — tooling, CI, dependencies

## Quality gates

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy src/playlist_sync`
- [ ] `uv run pytest -q` (offline)
- [ ] `reviewer` subagent: APPROVE
- [ ] `security-audit` subagent: SAFE TO COMMIT (when the task touches auth, secrets, storage, network, dependencies, CI or UI)

## Golden rules

- [ ] Additive only — no remove/delete/unlike/unfollow operations
- [ ] No vendor SDK imports in `domain/`, `core/`, `storage/`, `reporting/`
- [ ] Services are injected into the core (no hidden singletons)
- [ ] `plan` remains read-only
- [ ] No secrets, tokens, cookies or personal data in the repo, logs or fixtures
- [ ] Tests touch no network
- [ ] No telemetry or extra outbound calls
- [ ] `apply` never prompts

## Risks and deferred work

<!-- Known limitations, follow-up tasks (with roadmap IDs) or "none". -->

## Human review

- [ ] I reviewed the diff and the gate results
- [ ] CI is green
- [ ] Branch protection on `main` is enabled (PR + review, no direct pushes, no force-pushes)
- [ ] I am merging this PR (agents never merge)
