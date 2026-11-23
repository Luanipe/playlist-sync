#!/usr/bin/env bash
# Push the current task branch and open (or update) its pull request.
#
# This is the only push path allowed by opencode.json. It validates the branch,
# Conventional Commit title, clean working tree, base branch and issue link, and
# never force-pushes. It never merges or closes a PR.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/open_pr.sh --title "<type>(<task>): <summary>" \
                     --body-file <path> [--issue <number>] [--base main] \
                     [--draft] [--dry-run]

Branch names:
  task/P<phase>-T<n>-<slug>   roadmap task (title must include the task ID)
  chore|docs|fix|test|refactor|perf/<slug>   non-roadmap work

The body must contain "Closes #<issue>" when --issue is given.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

TITLE=""
BODY_FILE=""
ISSUE=""
BASE="main"
DRAFT=0
DRY_RUN=0

while (($# > 0)); do
  case "$1" in
    --title)
      [[ $# -ge 2 ]] || die "--title needs a value"
      TITLE="$2"
      shift 2
      ;;
    --body-file)
      [[ $# -ge 2 ]] || die "--body-file needs a value"
      BODY_FILE="$2"
      shift 2
      ;;
    --issue)
      [[ $# -ge 2 ]] || die "--issue needs a value"
      ISSUE="$2"
      shift 2
      ;;
    --base)
      [[ $# -ge 2 ]] || die "--base needs a value"
      BASE="$2"
      shift 2
      ;;
    --draft)
      DRAFT=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      die "unknown argument: $1"
      ;;
  esac
done

command -v git >/dev/null 2>&1 || die "git is not installed"

[[ -n "$BODY_FILE" ]] || die "--body-file is required"
[[ -f "$BODY_FILE" ]] || die "body file not found: $BODY_FILE"
[[ -s "$BODY_FILE" ]] || die "body file is empty: $BODY_FILE"
BODY_DIR="$(cd "$(dirname "$BODY_FILE")" && pwd)"
BODY_FILE="$BODY_DIR/$(basename "$BODY_FILE")"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || die "detached HEAD; switch to a branch first"
[[ "$BRANCH" != "main" && "$BRANCH" != "master" ]] || die "refusing to open a PR from $BRANCH"
[[ "$BRANCH" != "$BASE" ]] || die "refusing to open a PR from the base branch ($BASE)"

[[ "$BASE" == "main" ]] || die "--base only supports main (got: $BASE)"

TASK_ID=""
if [[ "$BRANCH" =~ ^task/(P[0-9]+-T[0-9]+)-[a-z0-9][a-z0-9-]*$ ]]; then
  TASK_ID="${BASH_REMATCH[1]}"
elif [[ "$BRANCH" =~ ^(chore|docs|fix|test|refactor|perf)/[a-z0-9][a-z0-9-]*$ ]]; then
  TASK_ID=""
else
  die "branch must be task/P<phase>-T<n>-<slug> or chore|docs|fix|test|refactor|perf/<slug>"
fi

[[ -n "$TITLE" ]] || die "--title is required"

if [[ -n "$TASK_ID" ]]; then
  [[ "$TITLE" =~ ^(feat|fix|test|docs|refactor|perf|chore)\($TASK_ID\):\ .+ ]] ||
    die "title must look like '<type>($TASK_ID): <summary>'"
  [[ -n "$ISSUE" ]] || die "task branches require --issue <number>"
else
  [[ "$TITLE" =~ ^(feat|fix|test|docs|refactor|perf|chore)(\([a-z0-9-]+\))?:\ .+ ]] ||
    die "title must be a Conventional Commit title, e.g. 'chore: ...'"
fi

if [[ -n "$ISSUE" ]]; then
  [[ "$ISSUE" =~ ^[0-9]+$ ]] || die "--issue must be a number"
  grep -Eq "(Closes|Fixes|Resolves) #$ISSUE([^0-9]|$)" "$BODY_FILE" ||
    die "the PR body must contain 'Closes #$ISSUE'"
fi

if [[ -n "$(git status --porcelain)" ]]; then
  die "working tree is not clean; commit or stash your changes first"
fi

git fetch origin "$BASE" --quiet

AHEAD="$(git rev-list --count "origin/$BASE..HEAD")"
((AHEAD > 0)) || die "no commits ahead of origin/$BASE"

git merge-base --is-ancestor "origin/$BASE" HEAD ||
  die "branch is behind origin/$BASE; rebase or merge the base branch first"

if ((DRY_RUN == 1)); then
  printf 'dry run: would push %s and open a PR against %s\n' "$BRANCH" "$BASE"
  exit 0
fi

command -v gh >/dev/null 2>&1 || die "gh (GitHub CLI) is not installed"

git push --set-upstream origin "HEAD:refs/heads/$BRANCH"

if PR_STATE_URL="$(gh pr view "$BRANCH" --json state,url --jq '.state + " " + .url' 2>/dev/null)"; then
  PR_STATE="${PR_STATE_URL%% *}"
  PR_URL="${PR_STATE_URL#* }"
  case "$PR_STATE" in
    OPEN)
      gh pr edit "$BRANCH" --title "$TITLE" --body-file "$BODY_FILE" >/dev/null
      printf 'updated PR: %s\n' "$PR_URL"
      exit 0
      ;;
    MERGED)
      die "a merged PR already exists for this branch: $PR_URL"
      ;;
    CLOSED)
      die "a closed PR already exists for this branch: $PR_URL (reopen it or use a new branch)"
      ;;
    *)
      die "unknown PR state '$PR_STATE' for $PR_URL"
      ;;
  esac
fi

CREATE_ARGS=(pr create --base "$BASE" --head "$BRANCH" --title "$TITLE" --body-file "$BODY_FILE")
if ((DRAFT == 1)); then
  CREATE_ARGS+=(--draft)
fi

gh "${CREATE_ARGS[@]}"
