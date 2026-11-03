# spec — Steps 1 and 2: the vision block, the question batch, the question bank
<!-- author: shrix -->

READ § Depths before Step 1 in every feature run. READ the rest at Step 1 in
lite, post-build mode and spec-only re-runs, and by the drill
(`references/think.md` § Drill) for the bank and the drill form. Step numbers
are `spec/SKILL.md`'s.

## Depths

A feature run goes at one depth, set before Step 2:

| depth | what it is | Steps 1–3 | Step 5 | about |
|---|---|---|---|---|
| `lite` (the default) | the pre-EGM /spec | the one batch of § Step 2; the recommended approach taken | one reviewer over the whole Checks table | 1–2 agents · ~65k–130k tokens |
| `EGM-lite` | a milder EGM-full | `references/think.md` at a smaller size: a drill of at most 3 turns, the concept gate, an idea panel of only Scope and reuse and Pre-mortem with the merger, the approach pick, the save point | one reviewer, as lite | 4–5 agents · ~250k–520k tokens |
| `EGM-full` | the think stage and the review panel | `references/think.md` | `references/review.md` § Panel | ~14 agents · ~0.8M–1.9M tokens · 15–25 min |

In lite, every step still runs, lighter: Step 4 writes only the spec
sections that apply (no N/A filler), each companion it triggers always inside
the spec — data and migration with rollback, the API contract, spike notes;
Step 5 runs ONE reviewer (round 2 only after a Critical stored-data or
interface fix). EGM-lite writes Step 4 as EGM-full does, and takes lite's
Step 5 and Step 6. Wherever the skill says lite about Step 5 or Step 6,
that covers EGM-lite too. The go, the filing and the safety gates are
unchanged.

**No depth word.** Before Step 2, the run checks two
triggers:

- **EGM-full** — the feature touches auth, secrets, user data or data that
  leaves the machine. User data = accounts, personal data about people, or
  content other people can see or send — not the project's own state,
  config, logs or check records, nor the owner's own local files; leaving
  the machine = sent over the network or to a third-party service (a push of
  the project's own repo excepted).
- **EGM-lite** — it changes stored data or a public interface, or it is not
  small. Small = one area of the code, about five plan tasks at most, nothing
  touching auth, secrets, user data or data that leaves the machine — an
  estimate from the request, made before any plan exists. Changing an
  interface = an existing call, endpoint or flag behaves differently; an
  addition that keeps every existing call working (a new flag, a new
  endpoint) is not one.

The EGM-full trigger holds → one line, and the run waits for the answer:

`depth: this <trigger> — recommended EGM-full. lite 1 agent ~65k · EGM-lite 4–5 agents ~250k–520k · EGM-full ~14 agents ~1.3M ~20 min — reply lite | EGM-lite | EGM-full`

Only the EGM-lite trigger → the run takes EGM-lite itself and prints
`depth: EGM-lite (this <trigger> — reply lite or EGM-full to change)`, with
no wait. No trigger → `depth: lite (reply EGM-lite or EGM-full to go
deeper)`, with no wait. Either way a reply before Step 4 may carry the word. A
deeper word in the batch's reply: the batch's answers become Decided and the
run enters `references/think.md` at § Drill (at § Concept gate when every
required topic is already answered). `lite` in a drill reply: the drill's
answers become Decided and the run asks § Step 2's batch for the CRITICAL
questions still open. `EGM-full` in a drill reply: the run goes on at
EGM-full — the 3-turn cap lifts and the idea panel runs in full. After the
drill, up to the save point, a word applies from the next step not yet run.
A word at or after Step 4 is the mid-run switch below.
Depth words match in any case (`egm-full` is `EGM-full`).
A depth word given → the word wins and no offer is made, but the run prints
`depth: <word> (from the word — reply lite | EGM-lite | EGM-full to change)`
before Step 2, so a feature that starts with the word can be corrected.

**A trigger found mid-run** (the EGM-full trigger) asks, at once and before the
next agent dispatch, `depth: <trigger> found — lite | EGM-full?` in a lite run
and `depth: <trigger> found — keep EGM-lite | EGM-full?` in an EGM-lite run; no
review runs until it is answered. `EGM-full` switches Steps 4 onward (companions,
the review panel), and the think stage is not replayed — except in an EGM-lite
run: found before the idea panel, `EGM-full` runs the rest of the think stage at
EGM-full. Nothing switches on its own.

**Edge cases.** Under "nonstop" the recommended depth is taken when it is
lite or EGM-lite, said in one line; EGM-full is asked once, as the one item no
work goes on without — the mid-run ask included. `lite think` and `EGM-lite think` are refused in one
line; `EGM-full think` is `think`, and `think` makes no offer. A resume of a
`draft — concept` with no word takes the concept's recorded depth
(`references/think.md` § Save point and resume); a word wins. Spec-only re-runs
and post-build mode make no offer.

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

## Step 2 (lite, post-build mode, spec-only re-runs): the batch

Ask the CRITICAL questions — the bank rows marked CRITICAL (not "in
EGM-full") — as ONE numbered batch, each with a recommended answer and why it
matters; skip any the request or the existing spec's Decided already answers.
Post-build mode asks only what § Post-build mode lists, and no batch when
nothing is left to ask. The user replies once,
"recommended" or per number. The replies are **Decided**; every other question
takes its recommended answer and becomes an **Assumption**, which Step 5
checks and Step 6 shows. "All questions" puts every question in the batch.

This batch is the run's one up-front ask: after the reply the run asks
nothing more until Step 6's go, which approves what was generated. A CRITICAL
decision found later becomes an Open question for that go, never a mid-run
stop. The one exception is the depth line (§ Depths), asked when a trigger is
found mid-run; the EGM-full offer, when its trigger holds, comes before the
batch.

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
| 5 | Scope (CRITICAL in EGM-full) | How is this done today, and why is that not enough? | Proves the problem is real; finds reuse |
| 6 | Constraint (CRITICAL in EGM-full) | What are the hard constraints (time, cost, platform, compatibility)? | Rules out approaches early |
| 7 | UX (HIGH) | Who are the primary users? | Shapes UX and errors |
| 8 | Data (HIGH) | What happens to old data when this ships? | Migration needs |
| 9 | Data (HIGH) | Offline or poor connectivity? | Caching/sync |
| 10 | Performance (MEDIUM) | Expected data volume? | Architecture |
| 11 | Integration (MEDIUM) | What existing systems does it connect to? | API contracts |
| 12 | Edge Cases (LOW) | Worst outcome if it breaks? | Error-handling investment |

## EGM-full: the drill form, one question per turn

```
❓ [question] — **Why asking**: [what it decides]
**Recommended**: [answer] — because [why it beats the others here]
**Other options**: A) … — trade-off: [gain · cost]   B) …
Reply with an answer, "recommended", or "recommended for the rest".
```
