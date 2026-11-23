---
description: Mirror docs/ROADMAP.md tasks as GitHub issues and refresh docs/ISSUES.md
---
Read `docs/ROADMAP.md` and `docs/AGENT_WORKFLOW.md`.

Run the roadmap -> issues helper:

```bash
python scripts/sync_roadmap_issues.py --dry-run
python scripts/sync_roadmap_issues.py
```

It creates one issue per pending task (title `P<phase>-T<n> — <title>`, labels `roadmap` and
`phase-<n>`), refreshes `docs/ISSUES.md`, and never closes or deletes anything. It only creates
missing labels and refuses a `--repo` that differs from `origin` unless `--allow-foreign-repo` is
passed. `--update` **replaces** existing issue bodies with the roadmap text, so human edits in the
body are lost. The dry-run needs `gh` auth and network (it lists the current issues).

Report: issues created, issues already present, and any task that could not be mirrored. Do not
edit `docs/ROADMAP.md` unless I ask you to. $ARGUMENTS
