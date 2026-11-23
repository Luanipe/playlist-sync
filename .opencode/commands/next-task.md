---
description: Implement the first unchecked task of the current phase, open a PR and stop
---
Read `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, then `docs/ROADMAP.md`.

Identify the current phase and its first unchecked task (`P<phase>-T<n>`). Read the docs relevant
to that task and find its GitHub issue in `docs/ISSUES.md` (run
`python scripts/sync_roadmap_issues.py` if the issue is missing). Briefly state your plan, then
implement it with tests.

Follow `docs/AGENT_WORKFLOW.md`:

1. If anything is ambiguous or conflicts with the docs, stop and ask me.
2. Create a branch from `origin/main`: `git fetch origin main` then
   `git switch -c task/P<phase>-T<n>-<slug> origin/main`.
3. Implement the task and its tests.
4. Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src/playlist_sync && uv run pytest -q`
   and fix every failure.
5. Run the `reviewer` subagent on the changes; fix every Blocker and Should-fix item, then re-run
   the gates.
6. If the task touches auth, secrets, storage, network, dependencies, CI or UI, run the
   `security-audit` subagent and fix every Critical/High finding.
7. Tick the task in `docs/ROADMAP.md`, then run `python scripts/sync_roadmap_issues.py` to refresh
   `docs/ISSUES.md`. Keep the tick if the PR is merged; revert it and rerun the sync if the PR is
   closed without merge.
8. Commit with a Conventional Commit that includes the task ID
   (e.g. `feat(P1-T03): add StreamingService interface`).
9. Write the PR body from `.github/pull_request_template.md` to a file under `/tmp/opencode/`,
   including `Closes #<issue>` and the gate/review/security results.
10. Open the PR with:

    ```bash
    scripts/open_pr.sh --title "<same Conventional Commit title>" \
      --body-file /tmp/opencode/pr-<task>.md --issue <issue-number>
    ```

11. Stop. Do not start the next task and never merge. Report the task ID, summary, gate results,
    review/security verdicts and the PR URL.

If git has no author identity configured, stop and report it instead of inventing one.

$ARGUMENTS
