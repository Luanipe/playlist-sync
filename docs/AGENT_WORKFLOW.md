# AGENT_WORKFLOW — AI-driven development

How autonomous agents (OpenCode) work on this repository. Read it together with `AGENTS.md`
(golden rules) and `docs/ROADMAP.md` (work queue).

Principles: **one task per invocation**, **tests with every change**, **review before commit**,
**local commits only**, and **stop and ask** when something is ambiguous or conflicts with docs.

## 1. Roles

| Agent | Mode | Purpose |
|---|---|---|
| **Primary (`build`)** | primary | Reads the task, implements it, runs the gates and commits. |
| **`architect`** | subagent | Plans a task: scope, files, interfaces, test plan, risks, open questions. Read-only. |
| **`reviewer`** | subagent | Reviews the diff against golden rules and docs, and runs the gates. Read-only. |
| **`security-audit`** | subagent | Audits secrets, credentials, privacy and destructive capabilities. Read-only. |

The review agents cannot edit files. Their shell access is limited to read-only `git` commands and
the quality gates. Configuration lives in `.opencode/agents/`.

## 2. The loop (one task)

1. **Select** — take the first unchecked task (`P<phase>-T<n>`) of the current phase in
   `docs/ROADMAP.md`.
2. **Read** — `AGENTS.md`, the task metadata, and the docs relevant to the task
   (`docs/PRD.md`, `ARCHITECTURE.md`, `MATCHING.md`, `AUTH.md`, `DECISIONS.md`).
3. **Plan** — restate the plan briefly. For non-trivial tasks, launch the `architect` subagent.
4. **Stop if ambiguous** — a missing decision, a doc/code conflict, a golden-rule change, or a
   task that needs credentials. Ask the human; do not guess.
5. **Implement** — code plus tests. Every new behavior has a test; tests never touch the network.
6. **Gate** — run and fix:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/playlist_sync
   uv run pytest -q
   ```

7. **Review** — launch the `reviewer` subagent. Fix every **Blocker** and **Should fix**, then
   re-run the gates and the reviewer until the verdict is APPROVE.
8. **Security** — launch the `security-audit` subagent when the task touches auth, secrets,
   storage, network, dependencies, CI or the UI. Fix every **Critical**/**High** finding.
9. **Record** — tick the task in `docs/ROADMAP.md` (and note anything deferred).
10. **Commit** — create one local Conventional Commit that includes the task ID, e.g.
    `feat(P1-T03): add StreamingService interface`.
11. **Stop** — do not start the next task. At the end of a phase, run `/phase-report` and summarize.

## 3. Gates

All of these must be green before a task is done:

- `uv run ruff check .` — no lint errors.
- `uv run ruff format --check .` — formatting is stable.
- `uv run mypy src/playlist_sync` — no type errors; `domain/` and `core/` are `--strict`.
- `uv run pytest -q` — all tests pass offline.

Phase acceptance criteria in `docs/ROADMAP.md` are additional and must hold at the end of a phase.

## 4. Git policy

- **Local commits only.** `git push` is denied in `opencode.json`; the human pushes.
- One task → one commit. Use Conventional Commits and include the task ID.
- Allowed types: `feat`, `fix`, `test`, `docs`, `refactor`, `perf`, `chore`.
- Never commit secrets, tokens, cookies, `.env`, `*.db`, browser profiles, reports or fixtures with
  personal data (see `.gitignore`).
- Never rewrite published history or force-push.
- If `user.name`/`user.email` are not configured, stop and report it; never invent an identity.

## 5. Escalation — stop and ask the human

- The task is ambiguous, or code and docs disagree.
- A change would affect a golden rule in `AGENTS.md`.
- A new architectural decision is needed (add an ADR to `docs/DECISIONS.md` in the same commit).
- The task requires credentials, a real API call, or a manual test by the owner.
- A gate cannot be fixed without changing scope.
- A reviewer verdict stays REQUEST CHANGES after a reasonable fix attempt.

## 6. Roadmap task format

Every task in `docs/ROADMAP.md` looks like this:

```markdown
- [ ] **P1-T03 — Short title** (`files/to/touch`; deps: P1-T02)
  - DoD: what must be true when the task is done (behavior + tests).
```

- IDs are stable: `P<phase>-T<number>`. Never renumber a completed task.
- `Deps:` lists tasks or phases that must be done first.
- `DoD:` is the task-level definition of done. The phase `**Accept:**` is the phase-level gate.
- `[ ]` = todo, `[x]` = done. An agent never ticks a task it did not finish and verify.

## 7. Commands

| Command | Purpose |
|---|---|
| `/next-task` | Implement the first unchecked task of the current phase, then stop. |
| `/autopilot` | One autonomous iteration: implement → gates → review → commit → stop. |
| `/check` | Run the four quality gates. |
| `/review` | Run the `reviewer` subagent on the current changes. |
| `/security` | Run the `security-audit` subagent on the current changes. |
| `/phase-report` | Report phase status, risks, open questions and the next step. |

## 8. Definition of done (per task)

- [ ] Behavior implemented as described in the docs and the task DoD.
- [ ] Tests added and passing offline.
- [ ] `ruff`, `ruff format`, `mypy` and `pytest` green.
- [ ] Reviewer verdict APPROVE (and security verdict SAFE TO COMMIT when applicable).
- [ ] No golden rule violated.
- [ ] `docs/ROADMAP.md` ticked; new decisions recorded in `docs/DECISIONS.md`.
- [ ] Local Conventional Commit created with the task ID.
