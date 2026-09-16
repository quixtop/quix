# mouter — build log

A record of how the `mouter` (model-router) skill was built, tested, and
installed, using the skill-creator loop. Written 2026-07-04.

## Goal

A global, agent-portable skill that maximizes output quality per usage
window on a flat-rate plan by keeping every model in its band of
comparative advantage — never above (quality risk), never below (wasted
capability) — and spending surplus capacity on background quality extras so
the main chat stays responsive. Every task's tier+effort is user-definable
in one config file; the capability toggles ON/OFF to coexist with other
skills; and it is portable across agents (Claude Code, Codex) via per-agent
adapter files.

## Architecture (as shipped)

- **SKILL.md** — logic only (~1,950 tok body, 162 lines). Numbered pipeline:
  state gate → load active adapter → classify to task key(s) → resolve
  tier+effort → execute (main lane interactive, extras background) → report
  → throttle. Zero tunables, zero agent-specific strings.
- **references/config.md** — THE single user-editable file: routing table
  (SDLC task key → {tier, effort}), execution caps, amplifier toggles,
  throttle order. Agent-agnostic.
- **references/claude.md, references/codex.md** — per-agent adapters; only
  the active one loads. Tier→model maps, effort mechanics, security pins,
  metering, and the subagent-generation setup step live here and ONLY here.
- **references/models.md** — agent-agnostic band definitions (floor/ceiling
  + two-sided failure reasoning per tier).
- **references/sdlc-matrix.md** — phase→key→tier rationale, examples, and
  band-violation traps in both directions.
- **references/amplifiers.md** — per-extra playbook (triggers, tier, prompt
  template, digest format, redundancy/skip rules).
- **references/state.json** — machine-written only (enabled flag + throttle
  override); the state gate's single source of truth.
- **scripts/** (stdlib only): `resolve_model.py` (request > config >
  default resolution, two-sided band audit, adapter pins, one-band
  availability fallback), `set_route.py` (prose-preserving config edits),
  `mouter_state.py` (state + throttle).

Tiers are abstract: **frontier / top / mid / light**. The Claude adapter
maps them to `fable / opus / sonnet / haiku`; the Codex adapter to
`gpt-5.5 / gpt-5.5 / gpt-5.4 / gpt-5.4-mini` (frontier+top collapse to one
model, differentiated by effort).

## Process followed (skill-creator loop)

1. **Capture intent** from the spec; flagged one deliberate deviation
   (portability override vs. the shrix `-x` convention, later reconciled —
   see Naming below).
2. **Live-doc research** (3 parallel agents) to ground the adapters.
   Corrections found vs. initial assumptions: a `fable` alias exists (no
   full-ID pin needed); Sonnet 5 is current mid (not 4.6); Codex reads
   `~/.agents/skills` natively (no symlink there); Opus 4.8 — not GPT-5.5 —
   currently leads Terminal-Bench 2.1.
3. **Draft** all files in a scratch dir.
4. **Script unit tests** — band warnings both directions, security pin
   caps frontier→top, reset-all, codex dry-run, availability fallback.
   One bug fixed (spurious `customized` flag after fallback); added
   throttle persistence to state.
5. **Behavioral evals** — 9 test cases (schema design, lint sweep, unit
   tests, security review, long refactor, composite feature, short
   feature, state-gate sequence, throttle) each run by an isolated
   subagent as a routing dry-run; graded by an independent grader agent.
6. **Human review** via the eval viewer, then **iterate**.
7. **Description-triggering optimization** — started, then stopped early
   (see Findings).
8. **Efficiency gate, validation, install, package.**

## Results

| Iteration | With-skill assertions | Baseline |
|---|---|---|
| 1 | 27/28 (the 1 fail was a wrong assertion, not the skill) | 0/5 |
| 2 | 32/32 after rewording 1 redundant-skip assertion | 0/5 |

Iteration-2 confirmed all three iteration-1 fixes: (1) no run
self-declared a fresh window — the fan-out concurrency cap held at 3 with
an explicit note; (2) `lint_sweep` resolves via `--task
boilerplate_scaffolding` with zero `fallback_route` bounces; (3)
redundancy skips (test_gap when the main lane IS test-writing;
security_sweep when the main lane IS a security review) are stated in one
line. Deterministic behavior (state gate, pins, band audits, one-band
fallback) was identical across all runs; variance was confined to the
judgment layer (extras applicability).

## Description-triggering: the key finding

The optimizer measured **precision 100%, recall ~0-8%**: mouter never
mis-fires on near-miss queries (k8s routing, model pricing, GPU picks all
correctly stay quiet), but it also under-fires on the dev tasks it should
catch. This is the documented meta-skill ceiling — Claude only consults a
skill for tasks it can't handle directly, and ordinary dev prompts don't
feel like they need a router first. No wording fixes this; the bottleneck
is the triggering mechanism, not the description. The loop was stopped
early (iteration 4/5) to conserve the user's flat-rate tokens, since it
was burning frontier-model quota for near-zero recall gain.

**Practical implication**: explicit `/mouter …` and the bare toggle always
work (direct invocation). The reliable usage pattern is `/mouter` once at
the start of a work session to flip ON, then it self-routes — rather than
relying on cold per-prompt semantic triggering.

## Naming / convention

Installed as `~/.agents/skills/mouter/` with a relative symlink
`~/.claude/skills/mouter -> ../../.agents/skills/mouter`. Per the user's
decision, the directory is plain `mouter` (not `-x`), and the shrix
identity convention is applied in frontmatter: `name: mouter`,
`author: shrix`, and a `(shrix)` prefix on the description.

## Known caveats / follow-ups (all optional)

1. **Frontmatter ~146 tok**, over the ≤100 target. The spec's comprehensive
   pushy trigger list and the 100-tok budget conflict; trimmed 188→146.
   Can cut to ~100 by dropping the subcommand enumeration + some cue words.
2. **Description optimization** was stopped early (above) — re-runnable, but
   recall is mechanism-limited regardless of wording.
3. **No formal isolated code-review** of the Python — skipped to conserve
   tokens. Scripts are compile-clean and functionally exercised
   (resolve/set/reset/state all confirmed through the installed symlink).
4. **Four `mouter-*` subagent files** (grunt/implementer/architect/
   reviewer) are NOT auto-created — the skill documents generating them as
   a consented setup step per the active adapter.
5. **claudifieds history repo** sync is the user's alone; untouched.

## Deliverables

- Installed skill: `~/.agents/skills/mouter/` (+ symlink at
  `~/.claude/skills/mouter`).
- Package: `mouter.skill` (127 KiB; SKILL.md at the `mouter/` zip root).
- Reports in `~/.agents/skills/mouter/docs/`: both benchmarks (md+json),
  both eval-review snapshots (self-contained HTML), the eval sets, and
  this build log.
