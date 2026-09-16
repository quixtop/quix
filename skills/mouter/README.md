# mouter — deployed architecture (ambient model routing)

One system, two halves:

- **Ambient half (hooks + statusline)** — recommends; never switches. Every
  prompt is classified; a mismatch renders a statusline chip; the USER
  switches via the native model picker (`/model`, `/effort`) — full context
  preserved, zero programmatic switching (the harness forbids it anyway).
- **Skill half (`SKILL.md` + scripts)** — explicit `/mouter` commands, the
  routing table, and the amplifier playbook (suggest-only; see the rule).

**Per-session:** OFF by default — `/mouter` activates the current session
(keyed by `CLAUDE_CODE_SESSION_ID`); `/mouter off all` / `on all` set every
session at once. Other sessions are never touched by a single toggle.

Perf split: python runs ONCE per prompt (hook, ~24ms); the ~300ms statusline
render loop pays only one jq (~4ms) — the hook pre-bakes everything the
compare needs into the reco (enriched: tier_idx, alias→tier array, effort
ladder, session_id).

## Naming convention

Every file deployed OUTSIDE this folder carries the `mouter` prefix so it is
recognizable as part of this system at a glance: `mouter-reco.sh`,
`mouter-reco.json`, `statusline.sh`, `mouter.md`. Inside the skill,
scripts use `mouter_*.py` / `resolve_model.py` / `set_route.py`.

## Component map

| Component | Path | Role |
|---|---|---|
| Skill (this folder) | `~/.agents/skills/mouter/` | logic home: SKILL.md, scripts, references |
| Hook shim | `~/.claude/hooks/mouter-reco.sh` | settings.json → skill glue (exec, stdin pass-through) |
| Hook wiring | `~/.claude/settings.json` → `hooks.UserPromptSubmit` | runs the shim on every prompt |
| Hook body | `scripts/mouter_hook.py` | classify → write/clear ENRICHED reco, atomically; never crashes (guards `SystemExit`) |
| Classifier | `scripts/mouter_classify.py` | prompt → task key; high-precision, silent-when-unsure |
| Resolver | `scripts/resolve_model.py` | task key → tier/effort/model (config > defaults; pins; fallback) |
| Reco file | `~/.claude/mouter-reco.json` | enriched handoff: hook writes, wrapper's jq reads; absent = no chip |
| Statusline wrapper | `~/.claude/bin/statusline.sh` | runs ~/.claude/statusline.py, appends chip via ONE guarded jq (no python in the render loop); propagates HUD exit code |
| Current-model source | the wrapper's OWN stdin (`.model.id`, `.effort.level`, `.session_id`) | live per render; also scopes the chip to this session |
| State gate | `references/state.json` via `scripts/mouter_state.py` | PER-SESSION ON/OFF (default off) + global throttle; `off`/`off all` clear the reco instantly |
| Switch keybind | `~/.claude/keybindings.json` | Ctrl+P → native model picker (↑↓ model, ←→ effort, Enter/`s`); CLI-only |
| Behavior rule | `~/.claude/rules/mouter.md` | chip is the only surface (CLI); amplifiers suggest-only; smooth switches |
| Response banner | hook stdout → model-visible context line | ALL surfaces (CLI + Desktop local): on mismatch the rule opens the response with a 3-line `model / effort (< reco'd)` banner (dashes = text+2, text centered), once per task; complements the CLI chip |
| Sibling rule | `~/.claude/rules/effort-calibration.md` | in-turn thinking depth (conscience to mouter's instrument) |
| Config | `references/config.md` | THE user-editable routing table (edit via `set_route.py`) |

## Data flow

```
prompt ──UserPromptSubmit──▶ mouter-reco.sh ──▶ mouter_hook.py
                                                  │ classify + resolve + enrich
                              ~/.claude/mouter-reco.json  (atomic; or cleared)
                                                  ▼
                                                  └─▶ stdout: ideal= + 3 pre-baked banner lines
                                                        └─▶ rule prints them VERBATIM iff
                                                              ideal model ≠ current (once/task)
statusline render ──▶ statusline.sh ──▶ statusline.py (own renderer)
                                └─▶ jq: own stdin vs reco ──▶ "▶ model·effort" (dim=match / normal=not) | ""
user switches via native picker (Ctrl+P) ──▶ next render: aligned ⇒ chip dims
```

Chip grammar: `▶ model·effort` — the IDEAL setting for the current task,
ALWAYS shown as JFYI calibration (no direction glyph; ignorable by design).
Two weights: **dim ▶** the ideal matches your current model/effort (recedes,
nothing to do) · **normal ▶** it does NOT match (stands out — you could
switch). Unknown current model also dims (nothing to advise). PERSISTENT:
follow-up prompts ("ok", questions)
keep the last task's chip alive — so you can see, mid-work, that you're
overusing a big model — until a new task reclassifies, you switch, 30 min
pass (TTL), or mute. Silent only when nothing trustworthy to say:
no/corrupt/stale reco, another session's reco, muted, or jq missing.

## Control

- Toggle / status / help: `/mouter` flips THIS session ON↔OFF (off by
  default); `/mouter off all` / `on all` set every session; `/mouter status`
  shows state; `/mouter help` prints the usage card. OFF clears the reco
  instantly → that session's chip/banner gone.
- Re-route a task class: `/mouter set <key>=<tier>[,<effort>]`; inspect with
  `/mouter table` / `/mouter status`.

## Test set

Automated (run after any change to the scripts):

```bash
python3 -B ~/.agents/skills/mouter/scripts/test_classify.py   # logic: 24 checks
bash ~/.agents/skills/mouter/scripts/test_deploy.sh           # weld: 23 checks (incl. per-session gate)
```

`test_classify.py` gates the python logic (keys, decoys, hook robustness);
`test_deploy.sh` gates the wiring AND the production bash/jq chip path
(overkill/underkill/aligned/effort-delta/unknown/corrupt/session fixtures —
stdin uses the real payload shape, effort as `{"level": ...}`).

Manual (live, ~2 min — the real proof):

0. **Activate first** — `/mouter` in the session (off by default).
1. **Chip appears** — type a task prompt, e.g. "add a --verbose flag to the
   logs command" → chip shows (on fable: normal-weight `▶ sonnet·high`).
2. **Self-clear on switch** — open the model picker, switch to the
   recommended tier → chip vanishes on the next render.
3. **Decoy silence** — "what's the pricing difference between opus and
   sonnet" → no chip.
4. **Mute gate** — `/mouter` (OFF) → chip gone immediately; `/mouter` (ON).
5. **Reco inspection** — after a task prompt: `cat ~/.claude/mouter-reco.json`.
6. **Skill intact** — `/mouter status` and `/mouter table` still answer.

## Teardown (full removal)

1. Remove the `mouter-reco.sh` entry from `hooks.UserPromptSubmit` in
   `~/.claude/settings.json`.
2. Point `statusLine.command` at `$HOME/.claude/statusline.py` (drops the chip).
3. Delete `~/.claude/hooks/mouter-reco.sh`, `~/.claude/bin/statusline.sh`,
   `~/.claude/mouter-reco.json`, `~/.claude/rules/mouter.md` (and the Sibling
   line in `effort-calibration.md`); remove the `ctrl+p` binding from
   `~/.claude/keybindings.json` if you no longer want it.
4. The skill folder itself is independent — keep or remove separately.
