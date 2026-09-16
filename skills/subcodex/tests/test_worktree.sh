#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$HOME/.agents/skills/_shared/tests/assert.sh"
WT="$DIR/scripts/worktree.sh"
REPO="$(mktemp -d)"; trap 'rm -rf "$REPO"' EXIT
git -C "$REPO" init -q
git -C "$REPO" config user.email t@t; git -C "$REPO" config user.name t
printf 'hello\n' > "$REPO/file.txt"
git -C "$REPO" add file.txt; git -C "$REPO" commit -qm init

# non-git dir → exit 65
NG="$(mktemp -d)"; assert_exit 65 bash "$WT" add "$NG" foo; rm -rf "$NG"

# add → worktree + branch exist
path=$(bash "$WT" add "$REPO" job1)
assert_contains "$path" "subcodex-worktrees/job1" "add prints worktree path"
[ -d "$path" ] && ok=yes || ok=no; assert_eq "$ok" "yes" "worktree dir exists"
git -C "$REPO" branch --list subcodex/job1 | grep -q job1 && b=yes || b=no
assert_eq "$b" "yes" "branch subcodex/job1 exists"

# make a change in the worktree, commit it
printf 'world\n' >> "$path/file.txt"
git -C "$path" commit -aqm "codex change"

# diff shows it
d=$(bash "$WT" diff "$REPO" job1); assert_contains "$d" "+world" "diff shows change"

# apply onto main repo working tree, UNSTAGED (porcelain shows ' M', not staged)
bash "$WT" apply "$REPO" job1
st=$(git -C "$REPO" status --porcelain file.txt)
assert_contains "$st" "file.txt" "apply brings change into main tree"
assert_eq "$(git -C "$REPO" diff --cached --name-only)" "" "apply leaves it unstaged"

# remove cleans up
bash "$WT" remove "$REPO" job1
[ -d "$path" ] && g=yes || g=no; assert_eq "$g" "no" "worktree removed"
assert_summary
