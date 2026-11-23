---
description: Autonomous loop for ONE roadmap task (implement, gates, review, commit, PR, stop)
---
You are running one iteration of the autonomous development loop. Follow
`docs/AGENT_WORKFLOW.md` exactly.

1. Pick the first unchecked task (`P<phase>-T<n>`) in the current phase of `docs/ROADMAP.md` and
   find its issue in `docs/ISSUES.md` (run `python scripts/sync_roadmap_issues.py` if missing).
2. Read `AGENTS.md` and the docs relevant to the task. If the task is ambiguous or conflicts with
   the docs, STOP and ask the human.
3. Optionally use the `architect` subagent to produce a plan for the task.
4. Get an up-to-date base and create the branch:
   `git fetch origin main && git switch -c task/P<phase>-T<n>-<slug> origin/main`.
5. Implement the task with tests.
6. Run and fix the gates:

   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run mypy src/playlist_sync && uv run pytest -q
   ```

7. Run the `reviewer` subagent on the changes. Fix all Blocker and Should-fix findings, re-run the
   gates and the reviewer until the verdict is APPROVE.
8. If the task touches auth, secrets, storage, network, dependencies, CI or UI, run the
   `security-audit` subagent and fix all Critical/High findings.
9. Tick the task in `docs/ROADMAP.md`, then run `python scripts/sync_roadmap_issues.py` to refresh
   `docs/ISSUES.md`.
10. Commit with a Conventional Commit including the task ID (e.g. `fix(P2-T04): ...`).
11. Write the PR body from `.github/pull_request_template.md`, including `Closes #<issue>`, and
    open the PR with `scripts/open_pr.sh --title "<commit title>" --body-file <path> --issue <n>`.
12. Stop. Do not start the next task and **never merge**. The human reviews and merges.

Report: task ID, summary of changes, gate results, review verdict, security verdict (if run) and
the PR URL. If anything is ambiguous or a gate cannot be fixed, stop and ask the human.

$ARGUMENTS
