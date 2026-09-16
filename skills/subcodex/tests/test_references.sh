#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$HOME/.agents/skills/_shared/tests/assert.sh"
R="$DIR/references"
get() { [ -f "$1" ] && cat "$1" || echo ""; }
assert_contains "$(get "$R/delegate-prompt.md")" "{{TASK}}" "delegate has {{TASK}} placeholder"
ew="$(get "$R/evaluate-write.md")"
assert_contains "$ew" "verify" "evaluate-write covers verify"
assert_contains "$ew" "could not run" "evaluate-write distinguishes couldn't-run"
er="$(get "$R/evaluate-readonly.md")"
assert_contains "$er" "sanity" "evaluate-readonly covers sanity-check"
h="$(get "$R/help.md")"
assert_contains "$h" "--write" "help documents --write"
assert_contains "$h" "--verify" "help documents --verify"
assert_summary
