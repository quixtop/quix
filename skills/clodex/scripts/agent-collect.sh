#!/usr/bin/env bash
# (c) Shrix
# author: shrix
# agent-collect.sh — clodex --panel: poll ONE codex agent to terminal state and write its result.
#   agent-collect.sh <statedir> <slot>
#   agent-collect.sh -h | --help | help
# Writes <slot>/status.txt and <slot>/result.md. Exits 0 when completed with a
# non-blank answer, 1 otherwise — the caller decides whether a dead agent aborts
# the panel. A job still running when the poll times out (POLL_TIMEOUT_SECS,
# default 1800 — clodex measures xhigh at 5–15 min per round, so 600 cut deep
# seats off mid-answer) is cancelled; a failed cancel prints a ✗ line on stderr.
# Seams: CODEX_SH, POLL, POLL_TIMEOUT_SECS.
set -uo pipefail
_gap() { [ -t 1 ] && printf '\n'; return 0; }
trap _gap EXIT
case "${1:-}" in -h|--help|help)
  awk 'NR==1 { next } /^# \(c\)/ { next } /^# author:/ { next } /^#/ { sub(/^# ?/,""); print; next } { exit }' "$0"
  exit 0 ;;
esac
has_text() { [ -f "$1" ] && grep -q '[^[:space:]]' "$1"; }   # -s is fooled by a lone newline
CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"
POLL="${POLL:-$HOME/.agents/skills/_shared/scripts/poll-job.sh}"
POLL_TIMEOUT_SECS="${POLL_TIMEOUT_SECS:-1800}"

STATEDIR="${1:-}"; SLOT="${2:-}"
[ -n "$STATEDIR" ] && [ -n "$SLOT" ] || {
  echo "usage: agent-collect.sh <statedir> <slot>" >&2; exit 64; }
D="$STATEDIR/$SLOT"
[ -d "$D" ] || { echo "agent-collect.sh: no slot dir: $D" >&2; exit 66; }

VENDOR=$(cat "$D/vendor.txt" 2>/dev/null)
[ "$VENDOR" = "codex" ] || {
  echo "agent-collect.sh: $SLOT is '$VENDOR' — collected by the orchestrator" >&2
  exit 3; }

JOB=$(cat "$D/jobid.txt" 2>/dev/null)
[ -n "$JOB" ] || { echo "agent-collect.sh: $SLOT has no jobid" >&2; exit 66; }
WS="${PANEL_WS:-$(pwd)}"

POLL_TIMEOUT_SECS="$POLL_TIMEOUT_SECS" bash "$POLL" "$WS" "$JOB" "$D/status.txt" >/dev/null 2>&1
STATUS=$(cat "$D/status.txt" 2>/dev/null)

# A timeout means Codex is still running the job: cancel it so it stops spending.
# </dev/null: a cancel must never read the caller's loop input.
if [ "$STATUS" = "timeout" ]; then
  if bash "$CODEX_SH" "$WS" cancel "$JOB" </dev/null >/dev/null 2>&1; then
    echo "agent-collect.sh: $SLOT timed out — cancelled job $JOB" >&2
  else
    echo "✗ agent-collect.sh: $SLOT timed out and cancelling job $JOB failed — it may still be running (or it finished just now)" >&2
  fi
fi

# The status payload nests under .job; a bare .summary is null.
S=$(bash "$CODEX_SH" "$WS" status "$JOB" --json 2>/dev/null)
printf '%s' "$S" | jq -r '.job.elapsed // .job.duration // "?"' > "$D/elapsed.txt"
printf '%s' "$S" | jq -r '.job.logFile // ""' > "$D/logfile.txt"
printf '%s' "$S" | jq -r '.job.summary // ""' > "$D/summary.txt"

# ⚠️ .job.summary is a SUMMARY, not the answer — measured at 198 chars against
# a 1582-char reply. Panel critiques quote specific claims, so a summary loses
# exactly the detail the judge needs. Take the log's "Final output" section and
# fall back to the summary only if the log is unreadable.
LOG=$(cat "$D/logfile.txt" 2>/dev/null)
if [ -n "$LOG" ] && [ -f "$LOG" ]; then
  sed -n '/^\[.*\] Final output$/,$p' "$LOG" | tail -n +2 \
    | sed '/^\[.*\] Turn completed\.$/d' > "$D/result.md"
fi
has_text "$D/result.md" || cp "$D/summary.txt" "$D/result.md" 2>/dev/null

if [ "$STATUS" = "completed" ] && has_text "$D/result.md"; then
  echo "$SLOT completed $(cat "$D/elapsed.txt")"; exit 0
fi
# Empty result on a 'completed' job is still a failure for panel's purposes —
# a phase cannot critique nothing. Any other status (timeout, failed, …) is kept.
[ "$STATUS" = "completed" ] && printf 'empty-result\n' > "$D/status.txt"
LOG=$(cat "$D/logfile.txt" 2>/dev/null)
[ -n "$LOG" ] && [ -f "$LOG" ] && tail -40 "$LOG" > "$D/error.log" 2>/dev/null
echo "$SLOT $(cat "$D/status.txt")"; exit 1
