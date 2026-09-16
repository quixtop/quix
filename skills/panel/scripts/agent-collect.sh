#!/usr/bin/env bash
# panel: poll ONE codex agent to terminal state and write its result.
#   agent-collect.sh <statedir> <slot>
# Writes <slot>/status.txt and <slot>/result.md. Exits 0 when completed,
# 1 otherwise — the caller decides whether a dead agent aborts the panel.
# Seams: CODEX_SH, POLL_TIMEOUT_SECS.
set -uo pipefail
CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"
POLL="${POLL:-$HOME/.agents/skills/_shared/scripts/poll-job.sh}"
POLL_TIMEOUT_SECS="${POLL_TIMEOUT_SECS:-600}"

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
[ -s "$D/result.md" ] || cp "$D/summary.txt" "$D/result.md" 2>/dev/null

if [ "$STATUS" = "completed" ] && [ -s "$D/result.md" ]; then
  echo "$SLOT completed $(cat "$D/elapsed.txt")"; exit 0
fi
# Empty result on a 'completed' job is still a failure for panel's purposes —
# a phase cannot critique nothing.
[ -s "$D/result.md" ] || printf 'empty-result\n' > "$D/status.txt"
LOG=$(cat "$D/logfile.txt" 2>/dev/null)
[ -n "$LOG" ] && [ -f "$LOG" ] && tail -40 "$LOG" > "$D/error.log" 2>/dev/null
echo "$SLOT $(cat "$D/status.txt")"; exit 1
