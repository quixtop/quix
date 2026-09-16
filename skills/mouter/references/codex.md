# OpenAI Codex adapter

Last verified: 2026-07-03 against https://developers.openai.com/codex
(models, config-reference, skills, pricing pages). Refresh: run the
`refresh` command — re-check model lineup, `model_reasoning_effort`,
skills paths, and plan limits, then update this file and this date.

## Tier map (machine-read by scripts/resolve_model.py)

```yaml
tiers:
  frontier: {model: gpt-5.5, weight: 10}
  top:      {model: gpt-5.5, weight: 10}
  mid:      {model: gpt-5.4, weight: 5}
  light:    {model: gpt-5.4-mini, weight: 1.5}
efforts: {low: low, medium: medium, high: high, xhigh: xhigh}
pins: {}
fallback_order: [frontier, top, mid, light]
```

**Frontier and top collapse to one model** (gpt-5.5). The differentiation
survives through effort: frontier-tier tasks run gpt-5.5 at `xhigh`
reasoning effort; top-tier tasks run it at the routed effort (usually
high/xhigh). State this in the routing justification rather than failing.

## Model notes (July 2026)

- **gpt-5.5** (frontier/top): OpenAI's recommended Codex default. $5/$30
  per MTok ($0.50 cached input), 1M context. Official: 82.7%
  Terminal-Bench 2.0 (SOTA at release), 58.6% SWE-bench Pro, 84.9% GDPval.
  Honesty note: on the third-party Terminal-Bench 2.1 leaderboard it
  scores 83.4% and does NOT currently lead (Claude Opus 4.8 leads at 88.0%).
- **gpt-5.4** (mid): $2.50/$15. Flagship for professional well-scoped work.
  (`gpt-5.3-codex` at $1.75/$14 still exists on the API but is DEPRECATED
  inside Codex with ChatGPT sign-in — do not route to it there.)
- **gpt-5.4-mini** (light): $0.75/$4.50. Explicitly positioned by OpenAI
  "for responsive coding tasks and subagents" — the parallel workforce.
  (`gpt-5.4-nano` $0.20/$1.25 is API-only, not Codex-selectable;
  `gpt-5.3-codex-spark` is a ChatGPT-Pro-only research preview.)

## Effort mechanics

`model_reasoning_effort` = `minimal | low | medium | high | xhigh` — set in
`~/.codex/config.toml`, per profile, or per invocation via
`codex -c model_reasoning_effort="high"`. All mouter effort levels map
directly (xhigh burns ~3-5x medium). Effort IS settable per invocation, so
spawned agents can carry their own effort.

## Mechanics

- **Skills**: Codex implements the Agent Skills standard natively and scans
  `$CWD/.agents/skills` → repo root → `$HOME/.agents/skills` → `/etc/codex/skills`.
  mouter's canonical install at `~/.agents/skills/mouter/` is therefore
  discovered with NO symlink needed. Invoke explicitly via `/skills` or a
  `$mouter` mention; implicit auto-selection also works. Per-skill disable:
  `[[skills.config]]` in config.toml.
- **Model selection**: `model = "gpt-5.5"` in config.toml, `--model`/`-m`
  per invocation, `/model` in the TUI.
- **Subagents / parallel**: `features.multi_agent` is stable and on by
  default — `spawn_agent`, `send_input`, `wait_agent`, `close_agent`;
  `agents.max_threads` (default 6) is the host-side fan-out ceiling
  (mouter's `fanout_cap` must stay at or below it). No named agent-definition
  files like Claude Code's — pass role prompts at spawn time instead; the
  four mouter roles (grunt/implementer/architect/reviewer) become spawn
  prompts with `-c model=...` + `-c model_reasoning_effort=...` overrides.
- **Metering**: ChatGPT-plan sign-in shares a rolling 5-hour window plus a
  weekly cap (Plus ≈ 15-80 gpt-5.5 msgs/5h; Pro ≈ 5x). API-key auth
  bypasses windows at pay-per-token rates. Reason in window burn on plans.
- **Security rerouting**: no equivalent constraint — no documented
  classifier-based model rerouting for Codex/API traffic (the consumer
  ChatGPT safety router does not apply). `pins` is therefore empty;
  security work routes per config like any other task.
- **Availability fallback**: gpt-5.5 unavailable → fall to gpt-5.4 per
  `fallback_order` (frontier/top share a model, so one band down lands on
  mid), announce, continue.
