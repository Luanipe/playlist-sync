---
description: Autonomous loop for ONE roadmap task (implement, gates, review, commit, stop)
---
You are running one iteration of the autonomous development loop. Follow
`docs/AGENT_WORKFLOW.md` exactly.

1. Pick the first unchecked task (`P<phase>-T<n>`) in the current phase of `docs/ROADMAP.md`.
2. Read `AGENTS.md` and the docs relevant to the task. If the task is ambiguous or conflicts with
   the docs, STOP and ask the human.
3. Optionally use the `architect` subagent to produce a plan for the task.
4. Implement the task with tests.
5. Run and fix the gates:

   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run mypy src/playlist_sync && uv run pytest -q
   ```

6. Run the `reviewer` subagent on the changes. Fix all Blocker and Should-fix findings, re-run the
   gates and the reviewer until the verdict is APPROVE.
7. If the task touches auth, secrets, storage, network, dependencies, CI or UI, run the
   `security-audit` subagent and fix all Critical/High findings.
8. Tick the task in `docs/ROADMAP.md`.
9. Commit locally with a Conventional Commit including the task ID (e.g. `fix(P2-T04): ...`).
   Never push.
10. Stop. Do not start the next task.

Report: task ID, summary of changes, gate results, review verdict, security verdict (if run) and
the local commit hash. If anything is ambiguous or a gate cannot be fixed, stop and ask the human.

$ARGUMENTS
