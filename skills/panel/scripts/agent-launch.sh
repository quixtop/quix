#!/usr/bin/env bash
# panel: launch ONE agent from a grammar token. Echoes a handle line the caller
# stores; the caller polls with agent-collect.sh.
#   agent-launch.sh <statedir> <slot> <token> <promptfile>
#     token = vendor:model[:effort][@job][=lens][×N]  (N handled by the caller —
#             it calls this once per instance with slot a1, a2, …)
# Only `codex` launches here. `cc` agents are spawned by the orchestrator via
# the Agent tool — a shell script cannot call it — so this exits 3 for cc and
# the caller handles it inline. Seam: CODEX_SH.
set -uo pipefail
CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"
LAUNCH="${LAUNCH:-$HOME/.agents/skills/_shared/scripts/launch-job.sh}"

STATEDIR="${1:-}"; SLOT="${2:-}"; TOKEN="${3:-}"; PROMPTFILE="${4:-}"
[ -n "$STATEDIR" ] && [ -n "$SLOT" ] && [ -n "$TOKEN" ] && [ -n "$PROMPTFILE" ] || {
  echo "usage: agent-launch.sh <statedir> <slot> <token> <promptfile>" >&2; exit 64; }
[ -f "$PROMPTFILE" ] || { echo "agent-launch.sh: no prompt file: $PROMPTFILE" >&2; exit 66; }

# ── parse the token ───────────────────────────────────────────────────────
# Strip modifiers first so a model name containing - or . is never mangled.
core="${TOKEN%%×*}"; core="${core%%\**}"     # drop ×N / *N
core="${core%%=*}"                            # drop =lens
core="${core%%@*}"                            # drop @job
VENDOR="${core%%:*}"
rest="${core#*:}"
MODEL="${rest%%:*}"
EFFORT=""
[ "$rest" != "$MODEL" ] && EFFORT="${rest#*:}"

D="$STATEDIR/$SLOT"; mkdir -p "$D"
printf '%s\n' "$TOKEN"  > "$D/token.txt"
printf '%s\n' "$VENDOR" > "$D/vendor.txt"
printf '%s\n' "$MODEL"  > "$D/model.txt"
printf '%s\n' "$EFFORT" > "$D/effort.txt"
cp "$PROMPTFILE" "$D/prompt.txt"

case "$VENDOR" in
  codex)
    WS="${PANEL_WS:-$(pwd)}"
    # --model / effort are forwarded only when set; an empty expansion would
    # otherwise pass a bare flag and the CLI would reject the launch.
    bash "$LAUNCH" "$WS" "$D" ${MODEL:+--model "$MODEL"} \
      ${EFFORT:+--effort "$EFFORT"} "$(cat "$PROMPTFILE")" > "$D/launch.log" 2>&1
    JOB=$(grep -oE 'task-[a-z0-9]+-[a-z0-9]+' "$D/launch.log" | head -1)
    if [ -z "$JOB" ]; then
      echo "agent-launch.sh: $SLOT no job-id; see $D/launch.log" >&2
      printf 'launch-failed\n' > "$D/status.txt"; exit 70
    fi
    printf '%s\n' "$JOB" > "$D/jobid.txt"
    echo "$SLOT codex $JOB"
    ;;
  cc)
    # Orchestrator spawns this one via the Agent tool.
    printf 'pending-agent-tool\n' > "$D/status.txt"
    echo "$SLOT cc agent-tool"
    exit 3
    ;;
  *)
    echo "agent-launch.sh: no adapter for vendor '$VENDOR'" >&2
    printf 'no-adapter\n' > "$D/status.txt"
    exit 69
    ;;
esac
