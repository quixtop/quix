#!/usr/bin/env bash
# (c) Shrix
# author: shrix
# agent-launch.sh — clodex --panel: launch ONE agent from a grammar token. Echoes a handle
# line the caller stores; the caller polls with agent-collect.sh.
#   agent-launch.sh <statedir> <slot> <token> <promptfile>
#   agent-launch.sh -h | --help | help
#     token = vendor:model[:effort][@job][=lens|/lens][×N]  (N handled by the caller —
#             it calls this once per instance with slot a1, a2, …)
# Only `codex` launches here. `cc` agents are spawned by the orchestrator via
# the Agent tool — a shell script cannot call it — so this exits 3 for cc and
# the caller handles it inline. Codex effort must be one Codex accepts
# (none · low · medium · high · xhigh) or the launch is refused — never
# `minimal`, which Codex rejects with HTTP 400 under its tool config.
# Exit: 0 launched · 3 cc (orchestrator spawns it) · 64 usage or bad effort ·
# 66 no prompt file · 69 no adapter · a launch-job.sh failure passes its own
# code through with a ✗ line: 71 no job-id but a job may be running (cancel it
# before any retry) · 72 `codex task` failed · 73 slot dir cannot be created.
# Seams: CODEX_SH, LAUNCH.
set -uo pipefail
_gap() { [ -t 1 ] && printf '\n'; return 0; }
trap _gap EXIT
case "${1:-}" in -h|--help|help)
  awk 'NR==1 { next } /^# \(c\)/ { next } /^# author:/ { next } /^#/ { sub(/^# ?/,""); print; next } { exit }' "$0"
  exit 0 ;;
esac
CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"
LAUNCH="${LAUNCH:-$HOME/.agents/skills/_shared/scripts/launch-job.sh}"

STATEDIR="${1:-}"; SLOT="${2:-}"; TOKEN="${3:-}"; PROMPTFILE="${4:-}"
[ -n "$STATEDIR" ] && [ -n "$SLOT" ] && [ -n "$TOKEN" ] && [ -n "$PROMPTFILE" ] || {
  echo "usage: agent-launch.sh <statedir> <slot> <token> <promptfile>" >&2; exit 64; }
[ -f "$PROMPTFILE" ] || { echo "agent-launch.sh: no prompt file: $PROMPTFILE" >&2; exit 66; }

# ── parse the token ───────────────────────────────────────────────────────
# Strip modifiers first so a model name containing - or . is never mangled.
core="${TOKEN%%×*}"; core="${core%%\**}"     # drop ×N / *N
core="${core%%=*}"; core="${core%%/*}"        # drop =lens or /lens
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
    case "$EFFORT" in ""|none|low|medium|high|xhigh) ;;
      *) echo "agent-launch.sh: codex does not accept effort '$EFFORT' — use none|low|medium|high|xhigh (never minimal: HTTP 400)" >&2
         printf 'bad-effort\n' > "$D/status.txt"; exit 64 ;;
    esac
    WS="${PANEL_WS:-$(pwd)}"
    # --model / effort are forwarded only when set; an empty expansion would
    # otherwise pass a bare flag and the CLI would reject the launch.
    # launch-job.sh prints only the job-id on stdout and writes $D/jobid.txt,
    # $D/logfile.txt and $D/launch.log itself; its status lines go to $D/launch.out.
    rc=0
    JOB=$(bash "$LAUNCH" "$WS" "$D" ${MODEL:+--model "$MODEL"} \
      ${EFFORT:+--effort "$EFFORT"} "$(cat "$PROMPTFILE")" 2>"$D/launch.out") || rc=$?
    if [ "$rc" -ne 0 ]; then
      printf 'launch-failed\n' > "$D/status.txt"
      echo "✗ agent-launch.sh: $SLOT launch failed (launch-job.sh exit $rc) — its reason:" >&2
      cat "$D/launch.out" >&2
      exit "$rc"
    fi
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
