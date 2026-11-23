# AGENT_WORKFLOW — AI-driven development

How autonomous agents (OpenCode) work on this repository. Read it together with `AGENTS.md`
(golden rules) and `docs/ROADMAP.md` (work queue).

Principles: **issue-driven**, **one task per invocation**, **one branch and PR per task**,
**tests with every change**, **review before the PR**, **human review before merge**, and
**stop and ask** when something is ambiguous or conflicts with docs.

## 1. Roles

| Agent / person | Mode | Purpose |
|---|---|---|
| **Primary (`build`)** | primary | Reads the task, implements it, runs the gates, ticks the roadmap and opens the PR. |
| **`architect`** | subagent | Plans a task: scope, files, interfaces, test plan, risks, open questions. Read-only. |
| **`reviewer`** | subagent | Reviews the diff against golden rules and docs, and runs the gates. Read-only. |
| **`security-audit`** | subagent | Audits secrets, credentials, privacy and destructive capabilities. Read-only. |
| **Human owner** | — | Reviews the PR, requests changes, merges, and has the final word. |

The review agents cannot edit files or spawn other subagents. Their shell access is limited to
read-only `git`/`gh` inspection; the reviewer may also run the quality gates. Configuration lives in
`.opencode/agents/`.

## 2. Issue-driven backlog

`docs/ROADMAP.md` is the source of truth for scope. Every **pending** roadmap task has a **1:1
GitHub issue**:

- Issue title: `P<phase>-T<n> — <task title>` (for example `P1-T02 — Domain models`).
- Labels: `roadmap` and `phase-<n>` (for example `phase-1`).
- Body: task ID, phase, files, dependencies, definition of done and a link to the roadmap.
- Mapping: `docs/ISSUES.md` (generated; do not edit by hand).

The helper is idempotent and only creates what is missing:

```bash
python scripts/sync_roadmap_issues.py --dry-run   # preview (needs gh auth + network)
python scripts/sync_roadmap_issues.py             # create missing issues + refresh the mapping
python scripts/sync_roadmap_issues.py --update    # also replace existing issue bodies
python scripts/sync_roadmap_issues.py --phase 1   # only create/update one phase
```

`--update` re-applies the roadmap title and replaces the whole issue body (human edits in the body
are lost). The helper refuses a `--repo` that differs from the `origin` remote unless
`--allow-foreign-repo` is passed, and it only creates missing labels (it never overwrites existing
ones).

Rules:

- Add new work to `docs/ROADMAP.md` first, with a stable `P<phase>-T<n>` ID, then run the sync.
- Never renumber a completed task and never rename an issue title without updating the roadmap.
- A task is done when its PR is **merged**. The PR body contains `Closes #<issue>`; GitHub closes
  the issue automatically on merge.

## 3. The loop (one task)

1. **Select** — take the first unchecked task (`P<phase>-T<n>`) of the current phase in
   `docs/ROADMAP.md`. Find its issue in `docs/ISSUES.md` (or `gh issue list --label roadmap`).
2. **Read** — `AGENTS.md`, the task's issue and DoD, and the docs relevant to the task
   (`docs/PRD.md`, `ARCHITECTURE.md`, `MATCHING.md`, `AUTH.md`, `DECISIONS.md`).
3. **Plan** — restate the plan briefly. For non-trivial tasks, launch the `architect` subagent.
4. **Stop if ambiguous** — a missing decision, a doc/code conflict, a golden-rule change, or a
   task that needs credentials. Ask the human; do not guess.
5. **Branch** — start from an up-to-date `main`:

   ```bash
   git fetch origin main
   git switch -c task/P1-T02-domain-models origin/main
   ```

   Work that is not a roadmap task (tooling, workflow, docs chores) uses
   `chore|docs|fix|test|refactor|perf/<slug>`. Never work directly on `main`.
6. **Implement** — code plus tests. Every new behavior has a test; tests never touch the network.
7. **Gate** — run and fix:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/playlist_sync
   uv run pytest -q
   ```

8. **Review** — launch the `reviewer` subagent. Fix every **Blocker** and **Should fix**, then
   re-run the gates and the reviewer until the verdict is APPROVE.
9. **Security** — launch the `security-audit` subagent when the task touches auth, secrets,
   storage, network, dependencies, CI or the UI. Fix every **Critical**/**High** finding.
10. **Record** — tick the task in `docs/ROADMAP.md` and note anything deferred. Then run
    `python scripts/sync_roadmap_issues.py` to refresh `docs/ISSUES.md` (it creates only missing
    issues and closes nothing). The tick means "implemented and submitted for review"; if the PR is
    closed without merge, revert it and rerun the sync.
11. **Commit** — create one Conventional Commit that includes the task ID, e.g.
    `feat(P1-T03): add StreamingService interface`.
12. **Open the PR** — write the body from `.github/pull_request_template.md` and use the helper:

    ```bash
    scripts/open_pr.sh \
      --title "feat(P1-T03): add StreamingService interface" \
      --body-file /tmp/opencode/pr-body.md \
      --issue 123
    ```

    The script validates the branch and title, refuses uncommitted work, pushes the branch without
    force and creates (or updates) the PR against `main`.
13. **Stop** — do not start the next task and **never merge**. Report the task ID, gate results,
    review/security verdicts and the PR URL. The human performs the review and the merge.

If the human requests changes, keep the same branch and PR: fix, re-run the gates and the review,
commit, then push the update with the same `scripts/open_pr.sh` command (it updates an existing
PR instead of creating a duplicate).

## 4. Branch, commit and PR policy

- Branch names: `task/P<phase>-T<n>-<slug>` for roadmap tasks,
  `chore|docs|fix|test|refactor|perf/<slug>` for everything else.
- **One task per branch and PR.** Do not mix unrelated changes or start the next task in the same
  PR.
- Commit types: `feat`, `fix`, `test`, `docs`, `refactor`, `perf`, `chore`. Include the task ID
  when there is one: `feat(P1-T03): ...`.
- PR title is the commit title. The body follows `.github/pull_request_template.md` and must
  include: summary, issue link (`Closes #N`), task ID/phase, gate results, reviewer verdict,
  security verdict when applicable, risks/deferred work and the human-review checklist.
- The PR targets `main` from the task branch. It must be ready for review and green in CI.
- **Agents never merge, never close a PR, never push to `main` and never force-push.**
- If a PR is closed without merge, revert the ROADMAP tick and leave the issue open.

## 5. Gates

All of these must be green before a task is done:

- `uv run ruff check .` — no lint errors.
- `uv run ruff format --check .` — formatting is stable.
- `uv run mypy src/playlist_sync` — no type errors; `domain/` and `core/` are `--strict`.
- `uv run pytest -q` — all tests pass offline.

Phase acceptance criteria in `docs/ROADMAP.md` are additional and must hold at the end of a phase.

## 6. Git and GitHub permissions

`opencode.json` is a **local guardrail, not a security boundary**. It denies direct `git push`,
PR merges/closes, issue deletions, raw `gh api`, and edits to the policy, the scripts and the
OpenCode definitions. Shell tooling can still execute code (for example `pytest`), so the real
boundary is **GitHub branch protection on `main`** (require a PR and review, block direct pushes and
force-pushes) together with the human review.

- Direct `git push` is denied. The only push path is `scripts/open_pr.sh`, which checks the branch
  name, the Conventional Commit title, the clean working tree, `--base main`, the task's
  `--issue`/`Closes #N`, and never uses force. Task branches must be
  `task/P<phase>-T<n>-<slug>`; other work uses `chore/`, `docs/`, `fix/`, `test/`, `refactor/` or
  `perf/`.
- `gh issue` is allowed for backlog management, but `close`, `delete`, `transfer`, `lock`, `unlock`,
  `pin` and `unpin` are denied. `gh pr` is allowed for reading, commenting and marking ready;
  `create`, `edit`, `merge`, `close` and raw `gh api` are denied (the helper creates/updates PRs).
  `gh label delete` and `gh label edit` are denied.
- The agent may `git fetch origin main`, `git switch` and `git commit`; it may not rewrite published
  history.
- The policy, `scripts/**`, `.opencode/**` and `.github/workflows/**` are **human-only**: edit
  denies prevent direct edits from weakening the guardrail (not code executed through allowed
  tooling — see above). The owner changes them in a reviewed PR.
- Never commit secrets, tokens, cookies, `.env`, `*.db`, browser profiles, reports or fixtures with
  personal data (see `.gitignore`).
- If `user.name`/`user.email` are not configured, stop and report it; never invent an identity.
- `scripts/open_pr.sh` and the issue helper are developer tools that require `gh` authentication and
  network access; the app itself still runs offline apart from the streaming services. The helper is
  bash-only (use Git Bash on Windows).
- `gh issue/pr … --body-file` publishes the named file verbatim to this public repository. Keep PR
  bodies under `/tmp/opencode/` and never point them at secrets or personal files; do not run
  untrusted code in the workspace.
- Direct `gh issue create/edit --repo <other>` can write to a repository the token can reach; the
  `--repo` origin guard only covers `scripts/sync_roadmap_issues.py`. Do not use a foreign `--repo`;
  the human review is expected to catch it.

## 7. Escalation — stop and ask the human

- The task is ambiguous, or code and docs disagree.
- A change would affect a golden rule in `AGENTS.md`.
- A new architectural decision is needed (add an ADR to `docs/DECISIONS.md` in the same PR).
- The task requires credentials, a real API call, or a manual test by the owner.
- A gate cannot be fixed without changing scope.
- A reviewer verdict stays REQUEST CHANGES after a reasonable fix attempt.
- The PR helper refuses a branch, title or body, or GitHub rejects the push/PR.

## 8. Roadmap task format

Every task in `docs/ROADMAP.md` looks like this:

```markdown
- [ ] **P1-T03 — Short title** (`files/to/touch`; deps: P1-T02)
  - DoD: what must be true when the task is done (behavior + tests).
```

- IDs are stable: `P<phase>-T<n>`. Never renumber a completed task.
- `Deps:` lists tasks or phases that must be done first.
- `DoD:` is the task-level definition of done. The phase `**Accept:**` is the phase-level gate.
- `[ ]` = todo. `[x]` = implemented, reviewed by the agent and submitted in a PR; the task is
  complete when the PR is merged (which closes its issue).

## 9. Commands

| Command | Purpose |
|---|---|
| `/next-task` | Implement the first unchecked task of the current phase, then open a PR and stop. |
| `/autopilot` | One autonomous iteration: implement → gates → review → commit → PR → stop. |
| `/sync-issues` | Create or refresh the GitHub issues that mirror `docs/ROADMAP.md`. |
| `/update-pr` | Push review fixes to the current task branch and update its PR. |
| `/check` | Run the four quality gates. |
| `/review` | Run the `reviewer` subagent on the current changes. |
| `/security` | Run the `security-audit` subagent on the current changes. |
| `/phase-report` | Report phase status, risks, open questions and the next step. |

## 10. Definition of done (per task)

- [ ] Behavior implemented as described in the docs and the task DoD.
- [ ] Tests added and passing offline.
- [ ] `ruff`, `ruff format`, `mypy` and `pytest` green.
- [ ] Reviewer verdict APPROVE (and security verdict SAFE TO COMMIT when applicable).
- [ ] No golden rule violated.
- [ ] `docs/ROADMAP.md` ticked; new decisions recorded in `docs/DECISIONS.md`.
- [ ] Issue exists and is referenced in the PR (`Closes #<issue>`).
- [ ] Dedicated branch and Conventional Commit with the task ID.
- [ ] PR opened against `main`, ready for human review.
- [ ] The agent stopped without merging.
