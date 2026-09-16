#!/usr/bin/env bash
# Manage subcodex git worktrees for isolated write tasks.
#   worktree.sh add    <repo> <slug>   -> create worktree+branch, print path
#   worktree.sh diff   <repo> <slug>   -> net diff of branch vs base
#   worktree.sh apply  <repo> <slug>   -> apply diff onto repo working tree (unstaged)
#   worktree.sh remove <repo> <slug>   -> remove worktree + branch
set -euo pipefail
CMD="${1:-}"; REPO="${2:-}"; SLUG="${3:-}"
[ -n "$CMD" ] && [ -n "$REPO" ] && [ -n "$SLUG" ] || {
  echo "usage: worktree.sh <add|diff|apply|remove> <repo> <slug>" >&2; exit 64; }
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || {
  echo "worktree.sh: not a git repo: $REPO" >&2; exit 65; }

git_common_dir="$(git -C "$REPO" rev-parse --git-common-dir)"
[ "${git_common_dir:0:1}" = "/" ] || git_common_dir="$REPO/$git_common_dir"
# Worktrees live under .git/ by default. SUBCODEX_WT_ROOT relocates the
# worktree tree itself to a permitted path, keyed by repo name so two repos
# never collide on a slug.
# ⚠️ This alone does NOT make --write work under a sandbox that denies .git
# writes: `git worktree add -b` still creates a ref in .git/refs/heads/, which
# fails independently of where the worktree lives. Read-only mode is
# unaffected — it uses the repo directly and never calls this script.
if [ -n "${SUBCODEX_WT_ROOT:-}" ]; then
  WT_ROOT="$SUBCODEX_WT_ROOT/$(basename "$REPO")"
else
  WT_ROOT="$git_common_dir/subcodex-worktrees"
fi
WT="$WT_ROOT/$SLUG"; BR="subcodex/$SLUG"; BASEF="$WT_ROOT/$SLUG.base"

case "$CMD" in
  add)
    mkdir -p "$WT_ROOT"
    base=$(git -C "$REPO" rev-parse HEAD)
    git -C "$REPO" worktree add -b "$BR" "$WT" "$base" >&2
    echo "$base" > "$BASEF"
    echo "$WT" ;;
  diff)
    base=$(cat "$BASEF" 2>/dev/null) || {
      echo "worktree.sh: missing base file $BASEF — refusing to diff against a guessed base" >&2; exit 67; }
    git -C "$WT" diff "$base" ;;
  apply)
    # plain apply → lands UNSTAGED in the working tree (no --index/--3way staging).
    # On conflict (parallel edits to the same files) apply fails non-zero; SKILL.md
    # catches that and resolves/surfaces it — conflict handling lives at the skill level.
    base=$(cat "$BASEF" 2>/dev/null) || {
      echo "worktree.sh: missing base file $BASEF — refusing to apply against a guessed base" >&2; exit 67; }
    git -C "$WT" diff "$base" | git -C "$REPO" apply - ;;
  remove)
    git -C "$REPO" worktree remove --force "$WT" 2>/dev/null || true
    git -C "$REPO" branch -D "$BR" 2>/dev/null || true
    rm -f "$BASEF" ;;
  *) echo "worktree.sh: unknown subcommand: $CMD" >&2; exit 64 ;;
esac
