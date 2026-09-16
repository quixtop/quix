#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$HOME/.agents/skills/_shared/tests/assert.sh"
f="$DIR/SKILL.md"; body="$([ -f "$f" ] && cat "$f" || echo "")"
# frontmatter
assert_contains "$body" "name: subcodex" "frontmatter name"
assert_contains "$body" "description:" "frontmatter description"
# required sections / behaviors (operationalizing the spec)
for tok in \
  "Disambiguation" "Confirm" "--write" "--verify" "worktree.sh" \
  "launch-job.sh" "poll-job.sh" "codex-preflight.sh" "registry.jsonl" \
  "MAX_CONCURRENT" "MAX_RETRIES" "unstaged" "evaluate-write" "evaluate-readonly" \
  "Non-git" "delegate-prompt"; do
  assert_contains "$body" "$tok" "SKILL.md covers: $tok"
done
assert_summary
