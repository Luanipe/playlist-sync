---
description: Implement the first unchecked task of the current phase (one task, then stop)
---
Read `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, then `docs/ROADMAP.md`.

Identify the current phase and its first unchecked task (`P<phase>-T<n>`). Read the docs relevant
to that task. Briefly state your plan, then implement it with tests.

Follow `docs/AGENT_WORKFLOW.md`:

1. If anything is ambiguous or conflicts with the docs, stop and ask me.
2. Implement the task and its tests.
3. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/playlist_sync && uv run pytest -q`
   and fix every failure.
4. Run the `reviewer` subagent on the changes; fix every Blocker and Should-fix item, then re-run
   the gates.
5. If the task touches auth, secrets, storage, network, dependencies, CI or UI, run the
   `security-audit` subagent and fix every Critical/High finding.
6. Tick the task in `docs/ROADMAP.md`.
7. Commit locally with a Conventional Commit that includes the task ID
   (e.g. `feat(P1-T03): add StreamingService interface`). Never push.
8. Stop. Do not start the next task.

If git has no author identity configured, stop and report it instead of inventing one.

$ARGUMENTS
