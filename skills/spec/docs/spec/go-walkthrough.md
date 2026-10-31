# /spec go walkthrough
Status: approved 2026-10-28 · built and reviewed 2026-10-28 — closed

## Open questions

None.

## 4.1 Feature Overview

```
Feature: go walkthrough

**One-Line Summary**: at Step 6's go, the user can answer "walk" and take
the review findings one per turn, instead of all in one block.
**Problem Statement**: the go shows every finding in one block; a Minor or a
fix nobody re-reviewed is easy to skim past, and acting on a few of them means
writing one long go-with-changes reply.
**Success Criteria**:
- A headless `/spec light` run with a seeded finding: "walk" shows one
  finding per turn; a `change` lands through ONE go-with-changes round; a
  plain "go" in a second run files at once, as today.
- `tests/skills/spec/test_spec.py` pins the walk's wording; the suite is green.
```

## 4.2 User Stories

```
As the owner at a /spec go
I want to take the open and unreviewed findings one at a time
So that each gets its own decision and none is skimmed past

**Acceptance Criteria**:
- [ ] Given a Review with findings in the walk set, when the go is asked,
      then "walk" is offered beside go / go with changes / no-go / drop it
- [ ] Given "walk", when each turn is answered, then the next finding follows,
      in the walk order, until the last or `stop`
- [ ] Given at least one `change`, when the walk ends, then ONE go-with-changes
      round applies all of them and the go is asked again
- [ ] Given no `change`, when the walk ends, then the go is asked again with
      no review round
- [ ] Given a plain "go", then nothing differs from today
```

## 4.3 Functional Requirements

```
FR1: Walk offered at the go
- **Priority**: High
- **Input**: the Review section's findings when Step 6 asks
- **Processing**: the walk set (FR2) is not empty → the go question names
  "walk" as one more answer
- **Output**: the go question with "walk"; an empty set → no "walk"
- **Constraints**: go, go with changes, no-go and drop it keep their meaning

FR2: The walk set, in order
- **Priority**: High
- **Processing**: 1) Critical findings still open; 2) every fix no later
  review saw — `fixed after round 2 — not re-reviewed`, light mode's
  `fixed — not re-reviewed`, round-1 fixes that stood on round 1 (no round 2
  ran over them), and a go-with-changes round's fixes; 3) Important findings
  logged open after round 2; 4) logged Minor findings. Findings closed by a
  re-reviewed fix or a refutation on the record are not walked
- **Output**: a numbered list, fixed when the walk starts

FR3: One finding per turn
- **Priority**: High
- **Output**: `Finding <i>/<n> · <severity> · <file or section>` — the
  finding in one or two lines, what was done about it, then the answers:
  `keep` · `change <how>` · `to tasks` · `stop`
- **Processing**: `keep` → as recorded; `change <how>` → recorded in Decided
  at once, marked `pending — walk`, and applied after the walk; `to tasks` →
  the finding is added to To file's tasks entries, marked `(from walk — not
  reviewed)` (the entry never takes a `provisional` mark), and its own
  Review entry is marked `to tasks — deferred`; for a fix already applied,
  the fix stays and the entry reads "re-review the fix for <finding>";
  `stop` → the rest are `keep`
- **Constraints**: one finding per turn. "go", "no-go" or "drop it" mid-walk
  is read as `stop`: a mid-walk go is never the go — Step 6 asks again. Any
  other reply → the same finding is shown again with the four answers; one
  that carries a change first gets: reply `change <how>` to record it

FR4: After the walk
- **Priority**: High
- **Processing**: one or more `change` → Step 6's go-with-changes path, once,
  over all of them (the `pending — walk` marks dropped, applied, plan
  re-invoked, ONE fresh review round over the touched sections); then the go
  is asked again with the full Step 6 block, To file word for word, and the
  next walk covers only that round's new findings. No `change` → the go is
  asked again at once, with the full block
- **Constraints**: no file is filed and no capture doc is written during the
  walk; it only writes the draft spec (Review, To file, Decided)

FR5: Record
- **Priority**: Medium
- **Output**: one line in the spec's Review per walk —
  `walk: <n> findings · kept <k> · changed <c> · to tasks <t>`
```

## 4.5 UI/UX Specification

A chat turn flow, no visual design:

```
**Interactions**:
1. Go asked: Step 6 block → "go · go with changes · walk · no-go · drop it"
2. "walk": Finding 1/n → answer → Finding 2/n … → last or `stop`
3. End: changes → one go-with-changes round → go asked again;
   none → go asked again
```

## 4.6 Technical Architecture

```
skills/spec/
├── SKILL.md                    Step 6: the go question names "walk"; a Walk
│                               bullet points to review.md (stays under the
│                               24,000-byte cap)
└── references/review.md        new § Walk at the go, after § Closing findings:
                                FR2–FR5
tests/skills/spec/test_spec.py  pins the wording of both
```

## Alternatives considered

```
Walk always runs before the go
- How: whenever the walk set is not empty, Step 6 walks it before asking
- Pros: no finding is ever skimmed
- Cons: every run pays the extra turns, even when the owner trusts the block
- Why rejected: the owner's pick is the opt-in reply; the plain go stays one turn
```

## 4.8 Edge Cases & Errors

```
Edge Case: "walk" with an empty walk set
- **Expected**: one line, "nothing to walk", and the go asked again

Edge Case: "go", "no-go" or "drop it" typed mid-walk
- **Expected**: read as `stop`; with changes recorded, the go-with-changes
  round runs first; then Step 6 asks again — a mid-walk go is never the go

Edge Case: `to tasks` on an open Critical
- **Expected**: allowed (the go can already pass with a Critical open); its
  Review entry reads `to tasks — deferred`, and the go block lists it first
  as deferred

Edge Case: a long walk that spans a compaction
- **Expected**: nothing is lost — each `change` is already in Decided as
  `pending — walk`, each `to tasks` already in To file

| Error | Cause | User Message | Recovery |
|-------|-------|--------------|----------|
| unknown reply | not one of the four answers | the same finding, answers listed again | answer again |
```

## 4.10 Testing Strategy

```
**Levels**: wording pinned in test_spec.py (unit); one headless proving run
(manual scenario: walk with a change; a plain go)
**What is hard to test, and how**: the turn flow — a `claude -p --continue`
run on a throwaway fixture, as in docs/spec/think-and-review-spikes.md
**Acceptance**: the two success criteria, each a plan task
```

## 4.11 Implementation Roadmap

Roadmap: see docs/plan/go-walkthrough.md

## 4.12 Risks & Mitigation

```
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| A long walk set makes many turns | Low | Low | `stop` ends it; Minor findings come last |
| A `change` loops (each round adds findings) | Low | Med | the next walk covers only that round's new findings, and `stop` or a plain go ends it |

**Rollback Plan**:
1. Revert the commit; the go is one block again.
```

## 4.13 Out of Scope

```
Explicitly Excluded:
- Walking the Open questions: they already take one answer each at the go. Future: No
- Walking findings closed by a re-reviewed fix or a refutation: settled. Future: No
```

## Decided

1. The walk covers the findings still open or fixed without a re-review, then
   the logged Minor ones, one per turn, answered `keep` · `change <how>` ·
   `to tasks`; after the last, the go question returns, and the changes are
   applied as ONE go-with-changes round.
2. Acceptance: a headless `/spec light` run with a seeded finding (walk with
   a change; a plain go files at once), plus the wording pinned in the tests.
3. No deadline or dependency; the proving run reuses the spikes' `claude -p`
   setup.

## Assumptions

- Approach: "walk" is an opt-in reply to the go (not a step that always runs).
- `stop` ends the walk early; "go" mid-walk reads as `stop`.
- The walk text lives in `references/review.md`; SKILL.md only points to it.

## Prerequisites

None.

## To file

- **reqs** (`skills/spec/docs/reqs.md`): At the go, "walk" takes the findings
  still open or fixed without a re-review, then the logged Minor ones, one per
  turn (`keep` · `change <how>` · `to tasks` · `stop`); the changes are applied
  as ONE go-with-changes round, and the go is asked again. A plain go is
  unchanged.
- **arch** (`skills/spec/docs/arch.md`): The walk lives in
  `references/review.md` § Walk at the go, beside § Closing findings; SKILL.md
  Step 6 points to it — why: findings are review.md's, and SKILL.md stays under
  its byte cap. The Flow chart gains `GO -->|walk| WK[walk: one finding per
  turn]`, `WK -->|changes| R` and `WK -->|none| GO`.
- **tasks** (`skills/spec/docs/tasks.md`): Build go-walkthrough —
  docs/plan/go-walkthrough.md; and remove "Walk through findings one by one at
  the go" (this spec covers it).

## Review

`single review: 1 agent · 129k tokens · 3 min` — light mode, one round:
0 Critical · 3 Important · 8 Minor, all fixed — not re-reviewed.
Write check: matched before and after (`8e8d192…`).

| # | sev | finding | outcome |
|---|---|---|---|
| 1 | Important | plan Task 2 pinned "or walk", which the dictated ask did not contain | fixed — not re-reviewed: ask reworded, pin `drop it or walk (when` |
| 2 | Important | FR2 missed unreviewed fixes (go-with-changes round, round-1 fixes standing on round 1) that Decided 1 promises | fixed — not re-reviewed: FR2 item 2 widened |
| 3 | Important | 4.8 "the Review line names it" contradicted the exact `walk:` line | fixed — not re-reviewed: the finding's own entry reads `to tasks — deferred` |
| 4 | Minor | FR4 wording missed the pinned "only that round's new findings" | fixed — not re-reviewed |
| 5 | Minor | go / no-go / drop it mid-walk undefined; a mid-walk go not stated as never the go | fixed — not re-reviewed: FR3 and 4.8 |
| 6 | Minor | 4.12 cited a "single re-ask" Step 6 does not have | fixed — not re-reviewed: clause dropped |
| 7 | Minor | walk-added To file entries unreviewed; re-asked go's block unstated | fixed — not re-reviewed: `(from walk — not reviewed)`, full Step 6 block |
| 8 | Minor | collected changes held nowhere; lost on compaction | fixed — not re-reviewed: Decided `pending — walk` at once; one `walk:` line per walk |
| 9 | Minor | Task 3 had no seed for a finding | fixed — not re-reviewed: toy fixture, re-run if the set is empty |
| 10 | Minor | "drop it" missing from the dictated ask | fixed — not re-reviewed |
| 11 | Minor | arch entry did not add the walk edges to the Flow chart | fixed — not re-reviewed |

**Build review** (dev Task 1, small tier): 0 C · 1 I · 5 M, all fixed and
test-pinned — a walked finding never re-enters a later walk; the walk turns
(not the change round) write only the draft; `to tasks` keeps an applied
fix and its mark is filed; `<n>` is the walk set size.

**Proving run** (2026-10-28, `claude -p --continue`, toy fixture, `/spec
light add a purge-old-notes command`; both runs switched to full mode, since
the purge deletes stored data; $15.14 in all, estimate was ~$3):

| check | result |
|---|---|
| "walk" offered at the go | ✅ both runs listed it beside go / go with changes / no-go / drop it |
| one finding per turn, in the walk order, pinned form | ✅ w1: `Finding 1/26 · Important · plan Global Constraints, Task 1`, then 2/26; the set held 18 round-1 fixes no later review saw, 3 Important and 5 Minor |
| `change` recorded at once as `pending — walk` | ✅ Decided 5, mark dropped once applied |
| `stop` keeps the rest; ONE go-with-changes round; go asked again with the full block | ✅ `walk: 26 findings · kept 25 · changed 1 · to tasks 0`; `go-with-changes: 1 agent · ~67k tokens · ~1 min`; nothing filed, Status still draft |
| the next walk covers only that round's new findings | ✅ offered over G1–G3 only |
| a plain "go" files at once | ✅ w2: spec and plan `approved`, capture docs written, no `walk:` line |

Seen, not a defect: in full mode the walk set grows with round 1's fixes
(26 here); Decided 1 includes them, and `stop` ends the walk.
