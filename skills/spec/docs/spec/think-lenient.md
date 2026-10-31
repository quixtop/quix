# /spec think lenient
Status: approved 2026-10-31

## Open questions

None (the one raised by the review is Decided 6).

## 4.1 Feature Overview

```
Feature: think lenient

**One-Line Summary**: the full-mode think stage asks less and runs fewer
idea lenses — the concept gate stops only for a CRITICAL inference or a
contradiction, the idea panel runs only the lenses the concept triggers, and
the approach pick asks only when approaches differ on scope or security.
**Problem Statement**: every full run stops at the concept gate, even when
nothing in it is in doubt; the idea panel always runs all 7 lenses
(`idea panel: 8 agents · ~450k tokens`), also lenses with nothing to attack
(Migration on a feature with no stored data, Monitoring on one that never
runs unattended); and the approach pick asks whenever approaches differ in
cost or user flow, which the go approves anyway.
**Success Criteria**:
1. The Model A/B's think sample, re-run headless on the toy fixture —
   `/spec think add tags to notes; the plugin system for future tag types is
   a must-have` — still challenges the plugin contract; Scope and reuse is
   among the lenses that ran; the concept gate either went on or stopped
   naming its reason (a required-topic row or a contradiction); the lenses
   that ran and were skipped match the set written down before the run
   (expected: Scope and reuse, Pre-mortem, Migration — `notes.json` gains
   tags —, Ease of use — the save and list flow changes —, Upkeep — the
   plugin system adds files; skipped: Cost and limits, Monitoring); the
   panel's own cost line and the turn's cost, with what that turn included,
   are recorded beside the A/B's panel-only $2.34 (Decided 4).
2. `python3 -B tests/skills/spec/test_spec.py` is green with the new pins;
   SKILL.md stays at most 24,000 bytes.
```

## 4.3 Functional Requirements

FR1: each idea lens says when it runs (Decided 1)
- **Processing**: every block under `references/lenses.md` § Idea lenses
  gains a fifth label after **Reads**, `**Runs**:`:
  - Scope and reuse — always.
  - Pre-mortem — always.
  - Migration and rollback — when stored data or a public interface changes.
  - Monitoring — when it runs unattended: hooks, background jobs, scheduled
    runs.
  - Cost and limits — when it calls agents, APIs or the network, or meets a
    size, rate or token limit.
  - Ease of use — when it changes a flow a person uses: a command, a prompt,
    a page.
  - Upkeep — when it adds files or dependencies, or files that must stay in
    step.
- **Output**: the review roles keep their four labels; only idea lenses
  carry **Runs**. **Runs** is for the dispatcher: a lens agent gets its
  block word for word WITHOUT the **Runs** line (lenses.md's intro says so),
  so it attacks the idea instead of judging whether it applies. The § Idea
  lenses intro says "the concept the gate passed" in place of "the
  confirmed concept".

FR2: the idea panel runs the triggered lenses (Decided 1)
- **Processing**: `references/think.md` § Idea panel runs, after the gate
  goes on or is confirmed, in ONE wave, each lens whose **Runs** line holds
  for the concept the gate passed — no cap; a trigger the run is unsure of
  counts as holding. With no optional trigger, the two always-lenses and the
  merger run. No lens is stopped early when others report first. Each
  skipped lens is named with its one-line reason, in the planned-spend line
  and in Review. A STOP recovery re-runs only lenses that ran. A self-review
  (no dispatch) covers the triggered lenses only. The user's first reply
  after the wave, before Step 4 starts, when it names skipped lenses, runs
  them as ONE extra wave plus a merger with its own planned-spend line, its
  problems routed as the first wave's (Decided 6); a later reply or a
  resumed concept takes no extra wave. Its lenses count against the panel's
  7 lens slots; its merger comes on top and is recorded, as a STOP
  recovery's does (two waves can reach 9 agents: 2 + 1, then 5 + 1). The
  panel runs no other second time.
- **Output**: the planned-spend line in `references/review.md` § Cap and
  cost reads `idea panel: <n> agents · ~<k>k tokens · skipped: <lens>
  (<reason>), …`, `<n>` counting the merger and `<k>` about 56 per agent
  (the measured ~450k over 8 agents); with no lens skipped it ends after the
  tokens. The idea panel's Review cost line gains the same `· skipped: …`
  tail. The 15-dispatch plan keeps the idea panel at most 8.

FR3: the concept gate stops only when it must (Decided 2)
- **Processing**: `references/think.md` § Concept gate shows the concept,
  Decided and the Assumptions in two labelled groups — "found in the request
  or the code — Decided if you confirm at a stop, else Assumptions until the
  go" and "recommended answers — stay Assumptions; the go approves them" —
  then:
  - it **stops** (confirm or correct) only when an Assumption found in the
    request or the code answers one of the drill's required-topic rows — 1,
    2, 4, 5 or 6 (scope, success, security, today, constraints) — naming
    those rows, or when § Contradictions applies;
  - otherwise it **goes on** in the same turn to the idea panel, and the
    found Assumptions stay Assumptions until the go.
  A correction updates Decided and shows the gate again; at a stop, a
  confirm moves the found group into Decided. No agent runs before the gate
  goes on or is confirmed. The gate decides when found Assumptions move, so
  § Drill's "an **Assumption** until the gate" (unchanged, Decided 5) means
  until the gate decides.

FR4: the approach pick asks only on scope or security (Decided 3)
- **Processing**: `references/think.md` § Approach pick: when the
  approaches differ in scope or security, the user picks, and the pick is
  **Decided** (an asking turn); otherwise — cost or user flow included — the
  recommended one is an **Assumption**, with the difference named beside it.

FR5: the turns that ask
- **Processing**: think.md's intro list reads: the drill's questions, the
  concept gate when it stops, at most 2 follow-ups after the idea panel, a
  contradiction, a lens STOP (`references/review.md` § Panel), and the
  approach pick when approaches differ on scope or security.
  SKILL.md's Quick Reference row 3 (full) reads `idea panel (triggered
  lenses), you pick on a scope or security difference, save point`.

FR6: pins
- **Processing**: `tests/skills/spec/test_spec.py` pins FR1–FR5's wording:
  `Lenses.test_lenses_shape` expects **Runs** as the fifth label on every
  idea lens and on no review role, and "always" on exactly Scope and reuse
  and Pre-mortem; `Think.test_think_rules` and the Cap and cost pins take
  the new text, with negative pins for "scope, security, cost or user flow",
  "Decided at the confirm" and `idea panel: 8 agents · ~450k tokens`; the
  cap-sum check in `Review.test_review_rules` reads the new "at most 8".

## 4.6 Technical Architecture

Rule edits only, no code: `references/lenses.md` (a **Runs** line per idea
lens: a lens is defined in one place), `references/think.md` (intro, § Concept
gate, § Idea panel, § Approach pick), `references/review.md` § Cap and cost
(the planned-spend line), SKILL.md Quick Reference row 3, and
`test_spec.py`.

## Alternatives considered

| approach | why not |
|---|---|
| a trigger table in think.md § Idea panel | splits each lens's definition across two files that can drift; lenses.md is where a lens is defined |
| a cap of 4 lenses, ranked by trigger strength | cheaper, but drops a triggered angle (Decided 1) |
| the user picks the lenses at the gate | adds a turn to a stage this feature makes ask less |
| start all lenses, stop the rest once the top 2 report clean | the agents finish together, so little is saved; the angles are independent, so the top 2 say nothing about the rest |
| an approach that differs on scope or security as an Open question at the go | one turn fewer, but a flip at the go rewrites the set and runs a go-with-changes round (Decided 3) |

## 4.8 Edge Cases & Errors

- A concept that triggers no optional lens → the two always-lenses and the
  merger run (3 agents), each skipped lens named.
- Every trigger holds → all 7 lenses run, as before.
- The gate goes on, and the panel then finds the concept wrong → it is
  routed as today (§ Idea panel): a follow-up, § Contradictions, an
  Assumption, Out of Scope or a Risk.
- The user corrects a found Assumption after the gate went on → it is not
  Decided, so § Contradictions does not apply: it becomes Decided at the
  next asking turn (a follow-up or the approach pick), or at the go as a go
  with changes; the panel does not re-run for it.
- A concept saved before this change and resumed → its panel already ran;
  nothing here applies to it.
- No agent dispatch available → § Self-review covers the triggered lenses
  only, with the skipped ones named.

## 4.10 Testing Strategy

Wording pins in `test_spec.py`, written first (they fail before the edit),
with negative pins that the old text is gone. One headless measured run of
the A/B think sample on the toy fixture (criterion 1), run as the
think-and-review spike notes' Task 1 describes (`claude -p` turn by turn in
a throwaway repo under the scratchpad, `--allowedTools` explicit).

## 4.11 Implementation Roadmap

`docs/plan/think-lenient.md`.

## 4.12 Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| a skipped lens was the one that would have caught the problem | Medium | Medium | Scope and reuse and Pre-mortem always run; an unsure trigger runs the lens; early sign: a Step 5 finding in a skipped lens's area |
| the gate goes on past an inference the user would have corrected | Low | Medium | only non-CRITICAL rows go on; they stay Assumptions, and the go approves them |
| trigger wording read too narrowly, so lenses are skipped that should run | Medium | Low | the skipped lenses and reasons are printed with the wave; a reply naming them runs them as one extra wave (Decided 6) |
| one headless sample does not show the trigger rules are right | Medium | Low | the expected run/skip set is written down before the run and compared after; the pins hold the wording |

## 4.13 Out of Scope

- The question drill (unchanged, as decided).
- The review panel's roles and the light single reviewer.
- A second sample that exercises the Migration trigger (offered, not taken).

## Decided

1. The idea panel runs Scope and reuse and Pre-mortem always, and every
   other lens on its trigger, with no cap; the planned-spend line names each
   skipped lens with its reason; no lens is stopped early (owner 31Oct26).
2. The concept gate stops only when an Assumption found in the request or
   the code answers a CRITICAL bank row — the drill's required-topic rows
   1, 2, 4, 5, 6 — or on a
   contradiction; otherwise it goes on, and the found Assumptions stay
   Assumptions until the go (owner 31Oct26).
3. Approaches that differ on scope or security are still picked by the user
   as a turn; a cost or user-flow difference takes the recommended one as an
   Assumption (owner 31Oct26).
4. Measured by re-running the Model A/B think sample headless on the toy
   fixture: the plugin contract still challenged, Scope and reuse ran, the
   gate went on or stopped with a stated reason; agent count and cost
   recorded against $2.34 (owner 31Oct26).
5. The question drill stays as it is (owner 31Oct26).
6. A reply on the next turn that names skipped lenses runs them as ONE extra
   wave plus a merger, inside the idea panel's cap of 8, recorded in Review;
   the panel runs no other second time (owner 31Oct26, at the go).

## Assumptions

- Approach: a **Runs** line per idea lens in lenses.md, read by think.md
  § Idea panel (the trigger-table alternative was not taken).
- `<k>` in the planned-spend line is ~56 per agent, from the measured ~450k
  over 8 agents.

## Prerequisites

None.

## To file

- **reqs** (`skills/spec/docs/reqs.md`, § Before the spec is written):
  replace the first two bullets with — In full mode, /spec runs a question
  drill (light offered on turn 1, taken only on an explicit yes), a concept
  gate, an idea panel of the triggered lenses (Scope and reuse and
  Pre-mortem always, the other five on their **Runs** line, no cap; each
  skipped lens named with its reason, and a reply naming skipped lenses runs
  them as one extra wave) with one merger, and an approach pick before it
  writes the spec. Light mode, post-build mode and spec-only re-runs skip
  this stage and keep one batch.
  — The only turns that ask in the think stage are the drill's questions,
  the concept gate when an inference answers a required-topic row (1, 2, 4,
  5, 6) or a contradiction applies, at most 2 follow-ups, a contradiction, a lens STOP
  and the approach pick when approaches differ on scope or security;
  routing the panel's problems and the save point need no extra confirm.
  Spec: `docs/spec/think-lenient.md`.
- **arch** (`skills/spec/docs/arch.md`, § Decisions): the bullet "One lens
  file serves both panels" gains — Each idea lens carries its own **Runs**
  trigger there, read by the dispatcher and left out of the lens's brief —
  why: a lens is defined in one place, so its trigger cannot drift from it.
- **arch** (`skills/spec/docs/arch.md`, Flow chart): the node `P[idea panel:
  7 lenses, merger]` becomes `P[idea panel: triggered lenses, merger]`, and
  the edge `G --> P` becomes `G -->|confirmed or nothing to check| P` — why:
  the panel size and the gate's stop now depend on the concept.
- **tasks** (`skills/spec/docs/tasks.md`): Build think-lenient —
  docs/plan/think-lenient.md.

## Review

`single review: 1 agent · 148k tokens · 4 min` — light mode, one round:
0 Critical · 3 Important · 11 Minor; 2 Important and 11 Minor fixed — not
re-reviewed (no round 2: no Critical stored-data or interface fix); 1
Important went to the go as Open question 1. Write check: matched before and
after (`000562d…`).

| # | sev | finding | outcome |
|---|---|---|---|
| 1 | Important | Task 3's "at most 8" wording breaks the cap-sum regex in `test_review_rules` | fixed — not re-reviewed: Task 3 updates the regex |
| 2 | Important | Task 2 named 2 of the 6 pins its edit breaks | fixed — not re-reviewed: every pin listed with its replacement; FR4 and FR5 keep the old pinned phrases |
| 3 | Important | the skip-objection mitigation has no path: the line never waits, the panel never re-runs | Decided 6 (go): an extra wave of named skipped lenses |
| 4 | Minor | "CRITICAL bank rows" also covers row 3 | fixed — not re-reviewed: "required-topic rows" |
| 5 | Minor | the found group's new label undefined | fixed — not re-reviewed: FR3 gives it |
| 6 | Minor | "the confirmed concept" false on the go-on path | fixed — not re-reviewed: "the concept the gate passed"; lenses.md in Task 1 |
| 7 | Minor | § Drill's "until the gate" now ambiguous | fixed — not re-reviewed: § Concept gate says it decides when they move |
| 8 | Minor | a lens agent would get its own Runs line | fixed — not re-reviewed: Runs left out of the brief |
| 9 | Minor | the Review record of skipped lenses has no form; reqs misses it | fixed — not re-reviewed: `· skipped:` tail; reqs clause |
| 10 | Minor | Task 1's "in order" needles ambiguous | fixed — not re-reviewed: lens → needle table |
| 11 | Minor | the headless allowlist is the one known to fall short | fixed — not re-reviewed: Phase 5 list plus scratchpad writes |
| 12 | Minor | the cost comparison is not like-for-like; no expected lens set | fixed — not re-reviewed: panel cost line recorded with what the turn held; expected set written before the run |
| 13 | Minor | no edge case for a correction after the gate went on | fixed — not re-reviewed: 4.8 entry |
| 14 | Minor | the approach has no arch To file entry | fixed — not re-reviewed: arch § Decisions entry |

### Acceptance

Expected before the run (criterion 1): run Scope and reuse, Pre-mortem,
Migration and rollback, Ease of use, Upkeep (5 lenses + 1 merger = 6
agents, ~336k tokens); skip Cost and limits, Monitoring.

| # | criterion | result | status |
|---|---|---|---|
| 1 | the A/B think sample, headless on the toy fixture | ran Scope and reuse, Ease of use, Migration, Upkeep, Pre-mortem; skipped Cost and limits ("no network or agent calls, small local data") and Monitoring ("nothing runs unattended") — the expected set; gate stopped naming rows 1, 4, 5, 6 (found F1–F4); plugin contract challenged (Scope and reuse: the registry costs more than the v1 goal needs, kept as Decided; M8: the plugin contract undefined); approach pick did not ask (no scope or security difference); `idea panel: 6 agents · 348k tokens · 2 min`, 1 C · 12 I · 4 M; write check matched | ✅ done |
| 2 | `test_spec.py` green; SKILL.md ≤ 24,000 bytes | 19 tests OK; 22,368 bytes | ✅ done |

Cost (claude 2.1.311, Opus 5.5 session, `total_cost_usd` is cumulative over
`--continue`, so each turn is its difference): drill $0.59 · gate $0.10 ·
panel turn $2.26 (sonnet lenses $0.82) · follow-up and save point $0.33 —
$3.28 to the save point in 4 turns. The A/B's panel turn was $2.34 with
sonnet $1.11: the lens share fell ~26 % (5 lenses for 7); the panel turn as
a whole is within one sample's noise of it. Run B (7 lenses, inline path)
reached its save point at $5.59 in 7 turns.
