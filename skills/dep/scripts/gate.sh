#!/usr/bin/env bash
# (c) Shrix
# author: shrix
# gate.sh — dep's change-gate: what changed since the last dep, and the stamp a
# complete dep writes.
#   gate.sh changed          the paths changed since the last dep, one per line
#   gate.sh base             the commit the last dep stamped, while it still resolves
#   gate.sh stamp [<commit>] write the stamp: <commit> (default HEAD), then one
#                            "<hash> <path>" or "deleted <path>" line per uncommitted path —
#                            none when <commit> is not HEAD, since that work was not shipped
#   gate.sh -h | --help | help
# changed = committed since the stamp ∪ uncommitted now ∪ the paths the stamp lists,
# minus every file still byte-identical to what the last dep shipped — so work
# shipped uncommitted is not shipped again, and a shipped file later reverted is.
# Paths are read NUL-separated, never quoted; a rename counts both its paths.
# No stamp, or a stamp whose commit no longer resolves (rebase, amend, squash):
# changed lists the uncommitted paths and exits 3 — add what this session edited.
# The stamp lives in the git folder ($(git rev-parse --git-path dep-stamp)), so it
# needs no gitignore and works in a linked worktree; it is written atomically.
# A stamp whose first line is not a full commit id counts as no stamp.
# Against the original inline gate in dep/SKILL.md, three outputs differ on
# purpose: a path named like an echo option (-n, -e) is listed, not dropped; a
# blank line in a malformed stamp is skipped, not printed as an empty path; and a
# first stamp line that is not a full commit id (an abbreviated sha or a ref
# name, only from a hand-edited stamp) counts as no stamp.
# Exit: 0 ok · 2 not a git repo · 3 no usable stamp · 64 usage.
set -uo pipefail
TMPD=""
_gap() { [ -t 1 ] && printf '\n'; return 0; }
trap '[ -n "$TMPD" ] && rm -rf "$TMPD"; _gap' EXIT
if [ $# -eq 1 ]; then case "$1" in -h|--help|help)
  awk 'NR==1 { next } /^# \(c\)/ { next } /^# author:/ { next } /^#/ { sub(/^# ?/,""); print; next } { exit }' "$0"
  exit 0 ;; esac
fi
# status: the bundle's proj-env.sh (TTY-guarded colour); a plain fallback if it is absent.
. "$(cd "$(dirname "$0")/../.." && pwd)/_shared/proj-env.sh" 2>/dev/null || status() {
  case "$1" in fail) printf '✗ %s\n' "$2" >&2 ;; warn) printf '⚠ %s\n' "$2" ;; *) printf '✓ %s\n' "$2" ;; esac; }
usage() { status fail "gate.sh: $1 — see gate.sh -h"; exit 64; }

top=$(git rev-parse --show-toplevel 2>/dev/null) || { status fail "gate.sh: not a git repo"; exit 2; }
cd "$top" || exit 2
STAMP=$(git rev-parse --path-format=absolute --git-path dep-stamp) || exit 2

dirty_paths() {   # uncommitted paths, one per line, never quoted
  git status --porcelain=v1 -z --untracked-files=all | while IFS= read -r -d '' rec; do
    printf '%s\n' "${rec:3}"
    case "${rec:0:2}" in *[RC]*) IFS= read -r -d '' o; printf '%s\n' "$o" ;; esac   # R/C, X or Y: old path
  done; }

stamped_commit() {   # the stamp's commit while it resolves, else fail
  local first; first=$(head -1 "$STAMP" 2>/dev/null) || return 1
  # only a full commit id: a symbolic "HEAD" (an old stamp from a repo with no
  # commits) would follow HEAD and bury work committed but never shipped
  case "$first" in ''|*[!0-9a-f]*) return 1 ;; esac
  [ ${#first} -eq 40 ] || [ ${#first} -eq 64 ] || return 1
  git rev-parse --verify --quiet "$first^{commit}"
}

cmd="${1:-}"; [ $# -gt 0 ] && shift
case "$cmd" in
  changed)
    [ $# -eq 0 ] || usage "changed takes no arguments"
    TMPD=$(mktemp -d "${TMPDIR:-/tmp}/gate.XXXXXX") || exit 2
    rc=0
    if base=$(stamped_commit); then :; else base=HEAD; rc=3; fi
    tail -n +2 "$STAMP" 2>/dev/null > "$TMPD/shipped"
    # a repo with no commit yet has no HEAD to diff against: the uncommitted paths alone
    git rev-parse --verify --quiet HEAD >/dev/null || { base=""; rc=3; }
    { [ -n "$base" ] && git diff --name-only --no-renames -z "$base"..HEAD | tr '\0' '\n'
      dirty_paths
      sed 's/^[^ ]* //' "$TMPD/shipped"; } | sort -u |
      while IFS= read -r p; do
        [ -n "$p" ] || continue
        if [ -e "$p" ]; then h=$(git hash-object -- "$p"); else h=deleted; fi
        grep -qxF -- "$h $p" "$TMPD/shipped" || printf '%s\n' "$p"   # unchanged since shipped → skip
      done
    [ $rc -eq 3 ] && echo "gate.sh: no usable stamp — add what this session edited" >&2
    exit $rc ;;
  base)
    [ $# -eq 0 ] || usage "base takes no arguments"
    stamped_commit || exit 3 ;;
  stamp)
    [ $# -le 1 ] || usage "stamp takes at most one commit"
    if [ $# -eq 1 ]; then sha=$(git rev-parse --verify --quiet "$1^{commit}") || usage "'$1' is not a commit"
    else sha=$(git rev-parse --verify --quiet HEAD) || { status fail "gate.sh: no commit to stamp yet"; exit 2; }; fi
    head_sha=$(git rev-parse --verify --quiet HEAD 2>/dev/null || true)
    tmp=$(mktemp "$STAMP.XXXXXX") || { status fail "gate.sh: could not write next to $STAMP"; exit 2; }
    { printf '%s\n' "$sha"
      # uncommitted work shipped with HEAD only; an older commit's ship did not include it
      [ "$sha" = "$head_sha" ] && dirty_paths | while IFS= read -r p; do
        if [ -e "$p" ]; then printf '%s %s\n' "$(git hash-object -- "$p")" "$p"; else printf 'deleted %s\n' "$p"; fi
      done; true; } > "$tmp" && mv "$tmp" "$STAMP" ||
      { rm -f "$tmp"; status fail "gate.sh: could not write $STAMP"; exit 2; }
    n=$(($(wc -l < "$STAMP") - 1))
    status ok "dep stamp written at ${sha:0:12} (+$n uncommitted path(s))" ;;
  "") usage "name a command" ;;
  *) usage "unknown command '$cmd'" ;;
esac
