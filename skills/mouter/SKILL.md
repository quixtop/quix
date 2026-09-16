---
name: mouter
author: shrix
description: "(shrix) Routes each task to the best-fit model tier and effort, running background quality agents on spare plan capacity. Triggers on \"mouter\" or its subcommands (status, config, table, set, reset, refresh, throttle, toggle); on which-model or how-much-effort questions; on usage caps or maximizing a flat-rate plan; on delegate/parallelize/background/subagent requests. Not for routing in the user's own code or model-pricing questions."
---

# mouter — model router

Maximize output quality per usage window: route every task to the tier and
effort where its band of comparative advantage lies — never above (quality
risk from cheap-but-wrong), never below (distinctive capability wasted at
heavy weight). Surplus capacity funds quality-amplifying extras in
background agents while the main chat stays responsive.

## 1. State gate (always first)

Run `python3 scripts/mouter_state.py get` before anything else. State is
PER SESSION (keyed by CLAUDE_CODE_SESSION_ID): OFF by default; `/mouter`
turns THIS session on; `on|off all` sets every session at once.

- **OFF and not explicitly invoked** → stand down SILENTLY. No routing, no
  extras, no subagents, no mention of mouter. The prompt is handled
  natively or by other skills. This is what lets mouter coexist with them.
- **OFF but explicitly invoked with a task** → ONE-SHOT: run the full
  pipeline for this task only; this session's state stays OFF.
- **ON** → auto-route every qualifying prompt through the pipeline (step 3
  onward). Never ask the user which model to use — that question is the
  failure mode this skill exists to remove.

## 2. Explicit commands (work regardless of state)

Invoked via the host agent's skill-invocation syntax (see the active
adapter's Mechanics section):

- **(bare)** — toggle ON↔OFF via `scripts/mouter_state.py toggle`; confirm
  in one line.
- **status** — state (ON/OFF) + status card: routing summary (defaults vs
  customizations from `scripts/resolve_model.py --table`), active/queued
  extras, pending proposed diffs, window estimate.
- **config** — print references/config.md in full.
- **table** — run `scripts/resolve_model.py --table`; render with
  customizations highlighted.
- **set task_key=tier[,effort]** — run `scripts/set_route.py set ...`
  (validates, warns on band violation but obeys, preserves prose). Works
  even when OFF.
- **reset task_key|all** — `scripts/set_route.py reset ...`.
- **refresh** — re-verify references/models.md and the ACTIVE adapter's
  model list against the vendor's live docs; update its "last verified"
  date.
- **throttle fresh|low|off** — manual override of the window-state
  heuristic via `scripts/mouter_state.py throttle ...`; persists until
  changed (step 8 honors it).
- **-h | --help** — print references/help.md verbatim; do NOT run the pipeline.
- **anything else** — treat as a task; force the full pipeline (one-shot
  if OFF).

## 3. Load the active adapter

Read the `agent` key from references/config.md (auto-detect from the host
environment where possible; config overrides). Load ONLY the named
adapter file `references/(agent).md` — the other adapters must cost zero
context. The
adapter supplies: tier→model map, effort mechanics, pins, fan-out and
background mechanics, metering shape, and setup steps.

## 4. Classify the prompt → task key(s)

1. Map the prompt to routing-table task keys. Composites decompose: "add
   feature X with tests and docs" → feature_well_scoped + unit_tests +
   docs_sync.
2. No matching key → config's `fallback_route`, announced in the routing
   justification.
3. Ambiguity → pick the closest key, state the choice so the user can
   correct it.
4. Unsure which key fits, or need the rationale/traps? Read
   references/sdlc-matrix.md.

## 5. Resolve tier + effort per key

Run `python3 scripts/resolve_model.py --task key1 --task key2 ...`
(add `--request-tier/--request-effort/--request-model` when the user named
one). The script enforces:

- **Resolution order**: model/tier named in the request > config routing
  entry > shipped default. Out-of-band requests are obeyed with the band
  violation stated in one line.
- **Two-sided band audit** — overkill ("short well-scoped → mid is
  quality-equivalent at a fraction of the weight, freeing extras budget")
  and underkill ("cross-file architecture on mid is below spec →
  escalating") both surface as one-line notes.
- **Adapter pins** — tier ceilings the adapter documents (e.g. security
  work); never silently exceeded.
- **Availability fallback** — unavailable model falls one band down,
  announced, and the task continues. Never fail a task over routing.
- Effort not independently settable on the host → the adapter's mapping
  degrades gracefully; note it in the justification, don't fail.

Band floors/ceilings and the reasoning behind them: references/models.md.

## 6. Execute

1. **Main lane** — the differentiated work runs interactive at its
   resolved tier/effort. It never de-escalates below band to save capacity
   unless the throttle forces it (extras always drop first). Discrete
   LIGHT-tier chunks that are self-contained are dispatched to a subagent
   at their own band instead of running inline on a higher main-lane model
   — routing to the correct band, not de-escalation, and automatic while
   mouter is ON (guards + rationale: `~/.claude/rules/mouter.md`
   § auto-delegation).
2. **Amplifiers** — OFFER the enabled extras from config's `amplifiers:`
   block that fit the task, in ONE line. They SPEND the usage window, so
   they are suggest-only, never auto-run; on explicit user opt-in, run them
   as BACKGROUND runs on their band-matched tiers,
   within config's `fanout_cap`. The raised `fanout_cap_fresh` applies ONLY
   when freshness is verifiable: the user set `throttle fresh`, or the host
   exposes a real usage-window signal. Never self-declare freshness —
   "feels like a new session" is not a signal, and self-granted raises are
   what the cap exists to prevent. Playbook per extra (triggers, prompts,
   digest formats): references/amplifiers.md.
3. Only genuinely independent units parallelize; dependent work
   serializes. Escalation is one-way: a failed extra reruns once, one tier
   up.
4. Hard rules for every background agent: working tree only — never
   commit, push, or stage; never write a shared file concurrently
   (serialize NOTES.md/README/changelog appends); non-mechanical changes
   are proposed diffs, never applied silently.
5. Use the host's prompt caching / batch lanes for non-interactive bulk
   work where the adapter documents them.

## 7. Report

- Up front: ONE line of routing justification in window-burn framing —
  what this routing frees or spends, and what the surplus buys.
- After opted-in extras complete: consolidated digest — checked / found /
  auto-fixed (mechanical only) / proposed diffs awaiting approval.

### Surfaces — the chip and the response banner

Routing is NEVER surfaced by recommending a model in chat, and never by
asking which model to use. Two ambient surfaces do it instead:

- **Statusline chip** `▶ model·effort` — the IDEAL setting for the current
  task, computed per prompt by an ambient hook. Dim `▶` = matches the
  current setting; normal `▶` = differs. Persists across follow-ups (30-min
  TTL) until a new task reclassifies or the user switches. No chip =
  session not activated, no recent task, or muted — silence is a feature.
- **Response banner** (CLI + Desktop-LOCAL; cloud VMs lack mouter files) —
  the hook emits `mouter: ideal=model/effort` plus 3 PRE-FORMATTED lines.
  When that ideal differs from the model actually running, OPEN the
  response with those 3 lines VERBATIM in a fenced block, once per task,
  never for follow-ups. Do NOT reformat, relabel, or add a suffix/arrow —
  the hook already sized and centred them. Ideal == current ⇒ no banner.

### Auto-delegation — the one thing ON does without asking

When a DISCRETE chunk resolves to the LIGHT tier (`resolve_model.py`:
boilerplate_scaffolding, docs_sync, commit_messages, pr_description,
release_notes, …) AND is self-contained enough to brief in a few lines,
dispatch it to a subagent at that tier (Agent tool `model` param) rather
than running it inline. Turning mouter ON is the whole opt-in; never ask
again per task.

Not a contradiction with `no-billed-defaults`: this SPENDS LESS than doing
the same work inline, and that rule guards EXTRA spend. Nor is it
de-escalation (§6.1) — light-tier work is routed to its OWN resolved band.
Work resolving to mid/top/frontier is NEVER delegated down to save capacity.

Guards — ALL must hold, else do it inline:
- bulk & self-contained. If briefing costs more than doing it (a one-line
  edit, a quick lookup, anything needing this conversation's context),
  delegation is a net LOSS.
- VERIFY the returned work before relaying it; a cheap model's output is
  still my responsibility.
- say so in one line ("delegated to haiku") so any quality or style
  difference is never mysterious.
- unsure which tier ⇒ do NOT delegate. Right-the-first-time beats
  cheap-and-twice.

The MAIN thread's model is never changed — conversational turns and small
edits still run on the session's model, by design. Any dispatch where the
model is picked here resolves tier/effort via `resolve_model.py`, never a
guess; security-flagged work pins to top (opus), never frontier.

## 8. Window-aware throttle

Track burn heuristically (session intensity, tier mix, fan-out); honor a
manual `throttle` override. When low, degrade per config's
`degradation_order`: fewer concurrent extras → extras down one band where
quality-equivalent → defer non-critical extras → last resort, main lane to
the adapter's documented low-effort inversion lane, announced. Verified
fresh window (`throttle fresh` or a host signal) + big task = spend
generously: raise fan-out to the fresh cap and offer the full amplifier
suite. Idle capacity is waste — but surplus buys MORE extras, never
gold-plating trivial work.

## Bundled resources

- references/config.md — THE user-editable file (routing, execution,
  amplifiers, throttle). Read when routing; edit only via
  scripts/set_route.py.
- references/claude.md, references/codex.md — per-agent adapters; load
  only the active one (step 3).
- references/models.md — band definitions and the two-sided failure
  reasoning. Read when a routing call needs justification.
- references/sdlc-matrix.md — phase→key→tier rationale, examples, traps.
  Read when classification is unclear.
- references/amplifiers.md — per-extra playbook. Read when queueing extras.
- references/help.md — the `/mouter -h` usage card.
- references/state.json — machine-written by scripts/mouter_state.py only.
- scripts/ — resolve_model.py (routing), set_route.py (config edits),
  mouter_state.py (state gate). Run them; don't reimplement their logic.

## Setup (first run on a new host)

1. Canonical install: `~/.agents/skills/mouter/` (the cross-agent skills
   convention). Link or register it per the host's skill-discovery rules —
   each adapter's Mechanics section documents its host's path and whether a
   symlink is needed.
2. OPTIONAL — generate the four routing subagent roles (grunt / implementer
   / architect / reviewer) per the ACTIVE adapter's setup section — they
   live OUTSIDE this package per host convention. Never overwrite an
   existing file without asking. (The Claude Code deployment skips these:
   it dispatches in-session subagents with per-dispatch model params.)
3. Adding a new host later = writing one new adapter file in references/;
   nothing else changes.
