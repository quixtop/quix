#!/bin/bash
# mouter deployment weld test — wiring + production chip path + per-session gate.
# Logic gates live in test_classify.py. Safe anytime: temp state + temp reco
# (MOUTER_STATE / MOUTER_RECO), a fake session id, and the wrapper's HUD seam
# (MOUTER_HUD_CMD=cat) keep the real state/cache untouched.
set -u
SKILL="$HOME/.agents/skills/mouter"
SETTINGS="$HOME/.claude/settings.json"
SHIM="$HOME/.claude/hooks/mouter-reco.sh"
WRAP="$HOME/.claude/bin/statusline.sh"
ST="$SKILL/scripts/mouter_state.py"
FAILS=0
chk(){ if [ "$2" -eq 0 ]; then echo "  PASS  $1"; else echo "  FAIL  $1"; FAILS=$((FAILS+1)); fi; }

TMPD=$(mktemp -d) || { echo "FAIL: mktemp -d failed"; exit 1; }
trap 'rm -rf "$TMPD"' EXIT
export MOUTER_RECO="$TMPD/reco.json"
export MOUTER_STATE="$TMPD/state.json"
export CLAUDE_CODE_SESSION_ID="weld-s1"        # the "current" session for on/off

echo "=== mouter deployment weld ==="

# 1. settings.json wiring (all matcher groups)
python3 - "$SETTINGS" <<'PY'; chk "settings.json: hook entry + statusLine -> wrapper" $?
import json, sys
d = json.load(open(sys.argv[1]))
cmds = [h["command"] for g in d["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
sys.exit(0 if (any("mouter-reco.sh" in c for c in cmds)
               and "statusline.sh" in d["statusLine"]["command"]) else 1)
PY
[ -x "$SHIM" ]; chk "shim exists + executable" $?
[ -x "$WRAP" ]; chk "wrapper exists + executable" $?

# 2. PER-SESSION gate --------------------------------------------------------
# default OFF: an un-activated session ignores task prompts
printf '{"prompt":"write unit tests for parser.py","session_id":"weld-s1"}' | "$SHIM" >/dev/null
[ ! -f "$MOUTER_RECO" ]; chk "default OFF: task in un-activated session -> ignored" $?

# activate this session
[ "$(python3 "$ST" on)" = "ON" ]; chk "/mouter on -> ON (this session activated)" $?

# activated + task -> enriched reco
OUT=$(printf '{"prompt":"write unit tests for parser.py","session_id":"weld-s1"}' | "$SHIM")
jq -e '.key=="unit_tests" and (.tier_idx|type=="number") and (.alias_tiers|type=="array")
       and .session_id=="weld-s1"' "$MOUTER_RECO" >/dev/null 2>&1
chk "activated + task -> enriched reco" $?

# baked banner on stdout: exactly ' model / effort', NO suffix/arrow
printf '%s' "$OUT" | grep -qxE ' sonnet / high' && ! printf '%s' "$OUT" | grep -qi "reco'd"
chk "banner: ' sonnet / high' baked, no suffix" $?

# isolation: a DIFFERENT session id is ignored even though weld-s1 is active
rm -f "$MOUTER_RECO"
printf '{"prompt":"write unit tests for parser.py","session_id":"weld-OTHER"}' | "$SHIM" >/dev/null
[ ! -f "$MOUTER_RECO" ]; chk "isolation: other session ignored (no reco)" $?

# decoy in activated session -> reco persists (continuity)
printf '{"prompt":"write unit tests for parser.py","session_id":"weld-s1"}' | "$SHIM" >/dev/null
printf '{"prompt":"what is the pricing of opus vs sonnet","session_id":"weld-s1"}' | "$SHIM" >/dev/null
[ -f "$MOUTER_RECO" ]; chk "activated + decoy -> reco persists" $?

# 3. chip matrix through the PRODUCTION wrapper (HUD seam = cat) -------------
NOW=$(date +%s)
RECO_MID='{"key":"unit_tests","tier":"mid","tier_idx":1,"effort":"high","model":"sonnet","session_id":"weld-s1","alias_tiers":[["fable",3],["opus",2],["sonnet",1],["haiku",0]],"efforts":["low","medium","high","xhigh"],"ts":'"$NOW"'}'
emit(){ printf '{"model":{"id":"%s"},"effort":{"level":"%s"},"session_id":"%s"}' "$1" "$2" "$3" | MOUTER_HUD_CMD=cat "$WRAP"; }
text(){ printf '%s' "$1" | perl -pe 's/\e\[[0-9;]*m//g' | grep -o '▶ [^ ]*'; }
kind(){ if ! printf '%s' "$1" | grep -qa '▶'; then echo none
        elif printf '%s' "$1" | grep -qaF $'\e[90m'; then echo dim; else echo normal; fi; }
shows(){ [ "$(text "$1")" = "$2" ] && [ "$(kind "$1")" = "$3" ]; }
printf '%s' "$RECO_MID" > "$MOUTER_RECO"
shows "$(emit claude-fable-5[1m] high weld-s1)" "▶ sonnet·high" normal; chk "chip: overkill -> ▶ sonnet·high NORMAL" $?
shows "$(emit claude-haiku-4-5 high weld-s1)" "▶ sonnet·high" normal; chk "chip: underkill -> NORMAL" $?
shows "$(emit claude-sonnet-5 high weld-s1)" "▶ sonnet·high" dim;    chk "chip: matches -> DIM" $?
shows "$(emit claude-sonnet-5 low weld-s1)" "▶ sonnet·high" normal;  chk "chip: effort delta -> NORMAL" $?
shows "$(emit some-unknown-model low weld-s1)" "▶ sonnet·high" dim;  chk "chip: unknown model -> DIM" $?
[ -z "$(text "$(emit claude-fable-5 high weld-OTHER)")" ];           chk "chip: session mismatch -> silent" $?
printf 'not json{{' > "$MOUTER_RECO"
[ -z "$(text "$(emit claude-fable-5 high weld-s1)")" ];              chk "chip: corrupt reco -> silent" $?
printf '%s' "${RECO_MID/\"ts\":$NOW/\"ts\":1000}" > "$MOUTER_RECO"
[ -z "$(text "$(emit claude-fable-5 high weld-s1)")" ];              chk "chip: stale reco (TTL) -> silent" $?
rm -f "$MOUTER_RECO"
! printf '%s' "$(emit claude-fable-5 high weld-s1)" | grep -q "▶";   chk "chip: no reco -> HUD untouched" $?

# 4. mute: /mouter off clears the reco AND gates the session ----------------
printf '%s' "$RECO_MID" > "$MOUTER_RECO"
[ "$(python3 "$ST" off)" = "OFF" ] && [ ! -f "$MOUTER_RECO" ]
chk "off: OFF + reco unlinked instantly" $?
printf '{"prompt":"write unit tests for parser.py","session_id":"weld-s1"}' | "$SHIM" >/dev/null
[ ! -f "$MOUTER_RECO" ]; chk "after off: activated-session task writes nothing" $?

# 5. off all / on all -------------------------------------------------------
python3 "$ST" on >/dev/null
printf '{"prompt":"write unit tests for parser.py","session_id":"weld-s1"}' | "$SHIM" >/dev/null
[ "$(python3 "$ST" 'off' all)" = "OFF (all sessions)" ] && [ ! -f "$MOUTER_RECO" ]
chk "off all -> OFF everywhere + reco cleared" $?
printf '{"prompt":"write unit tests for parser.py","session_id":"weld-s1"}' | "$SHIM" >/dev/null
[ ! -f "$MOUTER_RECO" ]; chk "off all -> even a previously-active session is off" $?
python3 "$ST" 'on' all >/dev/null
printf '{"prompt":"write unit tests for parser.py","session_id":"weld-NEVER"}' | "$SHIM" >/dev/null
[ -f "$MOUTER_RECO" ]; chk "on all -> default ON reaches a never-activated session" $?
python3 "$ST" 'off' all >/dev/null

echo
if [ "$FAILS" -eq 0 ]; then echo "ALL PASS"; else echo "$FAILS FAIL"; fi
exit "$FAILS"
