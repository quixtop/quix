# Tier bands — floors, ceilings, distinctive strengths

Agent-agnostic definitions. Concrete models, weights, and benchmark evidence
live in the active adapter (references/claude.md or references/codex.md) —
read the adapter for numbers; read this file for the reasoning.

## Why bands have two edges

Every tier has a floor and a ceiling, and both directions of mismatch are
failures:

- **Above the ceiling** (underkill): work harder than the tier can carry.
  The output looks plausible but is wrong or shallow — the most expensive
  outcome, because you pay again to redo it plus the cost of trusting it.
- **Below the floor** (overkill): work the tier's distinctive capability is
  wasted on. Quality is identical to a cheaper tier; the extra window burn
  buys nothing — it starves the amplifier budget that would have bought
  real quality elsewhere.

Where tiers perform equivalently on a task class, the higher tier is waste,
not quality. "Best model for the job" means best DIFFERENTIATED tier.

## FRONTIER — longest-horizon, hardest reasoning

- **Distinctive strength**: the lead over top GROWS with task length and
  complexity, and vanishes on short scoped tasks. Long multi-file
  refactors, greenfield system design, huge-context investigation,
  unfamiliar-codebase dives.
- **Floor**: genuinely long-horizon or deeply ambiguous work. A task a
  flagship handles equally well is below the floor — heaviest window
  weight for zero differentiation.
- **Ceiling**: none for reasoning depth; the constraint is weight and (per
  adapter) availability/predictability quirks.

## TOP — flagship workhorse

- **Distinctive strength**: judgment under ambiguity at sustainable weight —
  architecture within known bounds, decomposition, novel debugging,
  security judgment, high-blast-radius changes, long-context retrieval.
- **Floor**: multi-file scope, real ambiguity, or high blast radius.
  Single-file well-scoped work is below the floor.
- **Ceiling**: the frontier lane — very long horizon multi-file work where
  the frontier tier's documented lead applies.
- **Effort**: max available setting for architecture, security, and hard
  debugging — blast radius justifies it.

## MID — everyday implementation

- **Distinctive strength**: near-top quality on well-scoped implementation
  at a fraction of the weight. Standard refactoring, test writing, review
  drafting, and (per adapter evidence) computer-use/automation parity zones.
- **Floor**: anything needing actual code judgment — below this, light is
  quality-equivalent.
- **Ceiling**: architecture, novel debugging, long-horizon multi-file work.
  Watch for "simple-looking" tasks hiding cross-file coupling — the classic
  mid-tier trap.

## LIGHT — speed + volume

- **Distinctive strength**: the only tier cheap enough for many-way
  parallel. Lint, formatting, commit messages, log parsing, triage, doc
  stubs, bulk mechanical edits, high-volume amplifier extras.
- **Floor**: none — nothing is too small.
- **Ceiling**: cross-file reasoning or design judgment. One struggle
  signal → escalate immediately; cheap-but-wrong costs more than routing
  mid to begin with.

## Effort band-matching

Effort mirrors the tier rule: max effort on trivial work is waste; low
effort on hard work is underuse. Match effort to blast radius and
ambiguity, not to how important the task feels.

## Escalation — one-way by default

Cheaper tiers escalate UP on any struggle (a failed background extra reruns
one tier up). The main lane never de-escalates below band to save capacity
unless the throttle forces it — and then extras drop first.
