# Claude Code adapter

Last verified: 2026-07-03 against https://code.claude.com/docs and
https://platform.claude.com/docs. Refresh: run the `refresh` command — re-check
the model lineup, aliases, effort levels, and metering pages, then update this
file and this date.

## Tier map (machine-read by scripts/resolve_model.py)

```yaml
tiers:
  frontier: {model: fable, weight: 10}
  top:      {model: opus, weight: 5}
  mid:      {model: sonnet, weight: 3}
  light:    {model: haiku, weight: 1}
efforts: {low: low, medium: medium, high: high, xhigh: xhigh}
pins:
  security_review: top
fallback_order: [frontier, top, mid, light]
```

Aliases auto-track the recommended version — `fable` → Claude Fable 5
(`claude-fable-5`), `opus` → Opus 4.8, `sonnet` → Sonnet 5, `haiku` →
Haiku 4.5. Verified 2026-07-03: a `fable` alias EXISTS (earlier assumption
that Fable must be pinned by full ID is outdated). Pin full IDs only if an
alias ever tracks somewhere unwanted. Weights above are window-burn ratios
derived from API pricing (Haiku $1/$5 → 1x; Sonnet $3/$15 → 3x; Opus
$5/$25 → 5x; Fable $10/$50 → 10x per MTok in/out).

## Model notes (July 2026)

- **Fable 5** (frontier): ~95.0% SWE-bench Verified / 80.3% SWE-bench Pro /
  29.3% FrontierCode Diamond (announcement figures via secondary sources —
  not in first-party docs). 1M context, 128K output. Its lead GROWS with
  task length/complexity and vanishes on short scoped tasks. Requires
  Claude Code ≥ v2.1.170; unavailable under ZDR; never the session default.
- **Opus 4.8** (top): ~69.2% SWE-bench Pro (third-party leaderboard).
  1M context. Strongest long-context retrieval; leads Terminal-Bench 2.1
  (88.0%). Predictable — no classifier rerouting.
- **Sonnet 5** (mid): current Sonnet ($3/$15, intro $2/$10 through
  2026-08-31). 1M context. Near-Opus on well-scoped implementation and
  computer use at ~3/5 the weight.
- **Haiku 4.5** (light): 200K context, 64K output, fastest. The only tier
  cheap enough for many-way parallel fan-out.

## Security pin (Claude-specific rule)

`security_review` and anything security-flagged pins to **top (Opus), never
frontier**. Verified: Fable 5 runs cybersecurity/biology safety classifiers;
in Claude Code a flagged request auto-reruns on the default Opus model and
the session then STAYS on Opus until manually switched back. Security-heavy
repos can trip this from workspace context alone. Routing security work to
Fable is therefore unpredictable mid-session; Opus is deterministic. Treat
any task touching auth, secrets, exploits, or vuln analysis as
`security_review`-pinned even if classified under another key.

## Effort mechanics

Levels: `low | medium | high | xhigh | max` (Fable 5 / Sonnet 5 / Opus 4.8
support all five; unsupported levels fall back to the highest supported
at-or-below). Session default is `high`. Set globally via `/effort`,
`--effort`, or `effortLevel` in settings.json. Per subagent: the `effort`
frontmatter field in agent files ("inherits" by default) — so mouter's
effort routing IS independently settable per subagent on this host.
Throttle inversion lane: frontier-at-low-effort outscores top-at-xhigh on
SWE-bench Pro (75.0 vs 68.6, announcement figures) — the last-resort
degradation step.

## Mechanics

- **Invocation**: skills in `~/.claude/skills/` are invocable as
  `/mouter <args>`; arguments arrive as `$ARGUMENTS`. No separate command
  file is needed (custom commands and skills are merged).
- **Subagent files** go in `~/.claude/agents/` (user scope) — frontmatter
  supports `name`, `description`, `model` (aliases OK), `effort`,
  `background`. Generation is a setup step (below), never bundled.
- **Background execution**: subagents accept background execution natively
  (v2.1.198+ backgrounds by default); long shell commands support
  `run_in_background`. Fan-out is capped by config's `fanout_cap`.
- **Hooks** (optional, `hooks_auto_review`): configure `PostToolUse` /
  `Stop` hooks in `~/.claude/settings.json` to trigger review/test-gap
  amplifiers after edits. Leave off unless the user enables it.
- **Metering (Max plan)**: 5-hour rolling window + weekly caps (all-models
  plus a model-specific cap), shared across claude.ai, Claude Code,
  Desktop, and Cowork. Reason in window burn, not dollars.
- **claude.ai upload**: Settings → Capabilities/Skills → upload a ZIP with
  the skill folder at the ZIP root. Size cap undocumented (general 30MB
  file cap is the best-known proxy) — verify at upload time.
- **Availability fallback**: if `fable` is unavailable — rate/usage cap
  exhausted (the common case on Max: model-specific weekly caps), access
  gate, ZDR, or outage (it was offline 2026-06-12→07-01) — fall one band
  to `opus` per `fallback_order`, announce in one line, continue. Same
  rule down the ladder (opus → sonnet → haiku).

## Setup step: generate subagents (run once, with user consent)

Create `~/.claude/agents/` if missing. For each file below, if it already
exists, ASK before overwriting. Tier→model comes from the tier map above;
config routing still overrides per task at dispatch time.

`~/.claude/agents/mouter-grunt.md`
```markdown
---
name: mouter-grunt
description: Mechanical, high-volume work — lint sweeps, formatting, commit messages, doc stubs, bulk edits, triage. Parallel-safe; escalate up one tier on any struggle.
model: haiku
effort: low
---
Execute the mechanical task exactly as scoped. Work only in the working
tree — never commit, push, or stage. If the task turns out to need
cross-file reasoning or design judgment, stop and report that it needs a
higher tier instead of guessing.
```

`~/.claude/agents/mouter-implementer.md`
```markdown
---
name: mouter-implementer
description: Well-scoped implementation, standard refactors, test writing, automation, mid-weight amplifier extras.
model: sonnet
effort: high
---
Implement exactly what is scoped. Work only in the working tree — never
commit, push, or stage. If scope grows beyond the brief (architecture
choices, novel debugging, multi-file coupling), stop and report that it
needs a higher tier.
```

`~/.claude/agents/mouter-architect.md`
```markdown
---
name: mouter-architect
description: Design, decomposition, hard debugging, second opinions, high-blast-radius judgment.
model: opus
effort: xhigh
---
Do the differentiated thinking: design, decompose, debug, judge. Work only
in the working tree — never commit, push, or stage. Return decisions with
rationale and one alternative where the call is close.
```

`~/.claude/agents/mouter-reviewer.md`
```markdown
---
name: mouter-reviewer
description: Fresh-context independent review, security sweeps, high-stakes validation. Sees only the diff plus criteria.
model: opus
effort: xhigh
---
Review with fresh eyes: you get only the diff/artifact and the criteria —
no author context by design. Report findings as a digest (checked / found /
proposed); propose diffs, never apply non-mechanical changes, and never
commit, push, or stage.
```
