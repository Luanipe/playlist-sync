---
description: Push review fixes to the current task branch and update its pull request
---
You are addressing human review feedback on an existing PR. Follow `docs/AGENT_WORKFLOW.md`.

1. Confirm you are on the task branch (`git branch --show-current`) and that it matches
   `task/P<phase>-T<n>-<slug>` or `chore|docs|fix/<slug>`. Never switch to `main` to commit.
2. Implement the requested fixes with tests.
3. Run and fix the four gates:

   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run mypy src/playlist_sync && uv run pytest -q
   ```

4. Run the `reviewer` subagent (and `security-audit` if the change touches auth, secrets, storage,
   network, dependencies, CI or UI) and fix Blocker/Critical findings.
5. Update the PR body from `.github/pull_request_template.md` if the scope, risks or verdicts
   changed. Keep `Closes #<issue>`.
6. Commit with a Conventional Commit and push the update through the helper (it updates the
   existing PR instead of creating a duplicate):

   ```bash
   scripts/open_pr.sh --title "<same Conventional Commit title>" \
     --body-file /tmp/opencode/pr-<task>.md --issue <issue-number>
   ```

7. Add a short PR comment summarizing what changed, if that helps the reviewer. Stop; never merge.

$ARGUMENTS
