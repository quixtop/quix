# spec — Steps 1 and 2: the vision block, the question batch, the question bank
<!-- author: shrix -->

READ at Step 1 in light mode, post-build mode and spec-only re-runs, and by
the full-mode drill
(`references/think.md` § Drill) for the bank and the drill form. Step numbers
are `spec/SKILL.md`'s.

## Step 1: the vision block

```
🎯 Feature Vision:
**Request**: [restated]
**Goal**: [the problem solved]
**User Benefit**: [why users want it]
**Approach**: [general strategy, 1–2 sentences]

✅ Known: [clear requirements]
❓ Unclear: [ambiguity — why it matters]
```

## Step 2 (light mode, post-build mode, spec-only re-runs): the batch

Ask the CRITICAL questions — the bank rows marked CRITICAL (not "in full
mode") — as ONE numbered batch, each with a recommended answer and why it
matters; skip any the request or the existing spec's Decided already answers.
Post-build mode asks only what § Post-build mode lists, and no batch when
nothing is left to ask. The user replies once,
"recommended" or per number. The replies are **Decided**; every other question
takes its recommended answer and becomes an **Assumption**, which Step 5
checks and Step 6 shows. "All questions" puts every question in the batch.

This batch is the run's one up-front ask: after the reply the run asks
nothing more until Step 6's go, which approves what was generated. A CRITICAL
decision found later becomes an Open question for that go, never a mid-run
stop.

```
📋 Critical clarifications (N):

1. ❓ [question] — **Why asking**: [what it decides]
   **Recommended**: [answer] — because [why it beats the others here]
   **Other options**: A) … — trade-off: [what it gains · what it costs]
                      B) … — trade-off: [what it gains · what it costs]
2. ❓ …

Reply "recommended" for all, or per number.
```

## The bank

Questions, in priority order — pick those that fit the feature:

| # | Priority | Question | Why it matters |
|---|---|---|---|
| 1 | Scope (CRITICAL) | What's the simplest version that delivers value? | Prevents scope creep |
| 2 | Scope (CRITICAL) | How will we measure if this worked? | Feature-level acceptance criteria |
| 3 | Scope (CRITICAL) | Are there deadlines or external dependencies? | Affects phasing |
| 4 | Security (CRITICAL) | Who should NOT have access to this? | Security boundaries |
| 5 | Scope (CRITICAL in full mode) | How is this done today, and why is that not enough? | Proves the problem is real; finds reuse |
| 6 | Constraint (CRITICAL in full mode) | What are the hard constraints (time, cost, platform, compatibility)? | Rules out approaches early |
| 7 | UX (HIGH) | Who are the primary users? | Shapes UX and errors |
| 8 | Data (HIGH) | What happens to old data when this ships? | Migration needs |
| 9 | Data (HIGH) | Offline or poor connectivity? | Caching/sync |
| 10 | Performance (MEDIUM) | Expected data volume? | Architecture |
| 11 | Integration (MEDIUM) | What existing systems does it connect to? | API contracts |
| 12 | Edge Cases (LOW) | Worst outcome if it breaks? | Error-handling investment |

## Full mode: the drill form, one question per turn

```
❓ [question] — **Why asking**: [what it decides]
**Recommended**: [answer] — because [why it beats the others here]
**Other options**: A) … — trade-off: [gain · cost]   B) …
Reply with an answer, "recommended", or "recommended for the rest".
```
