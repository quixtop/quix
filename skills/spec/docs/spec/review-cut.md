# /spec review cut
Status: approved 2026-10-31 · built 2026-10-31

## Open questions

None.

## 4.1 Feature Overview

```
Feature: review cut

**One-Line Summary**: fewer review agents in /spec, with the same catches —
a light run keeps a local stored-data change on one reviewer.
**Problem Statement**: a light run with any companion trigger (a schema or
stored-data change, a new interface, a spike) switches to full: a 6-agent
review panel, ~330k–450k tokens in place of one reviewer (~65k).
**Success Criteria**:
1. One reviewer, briefed as § Single reviewer says (light mode, § Checks as
   built), over `tests/skills/spec/fixtures/toy/seeded-spec.md` — told there
   is no plan, the plan-only rows skipped as § Standalone review lists them,
   and the brief naming no seed — flags the missing rollback (an in-place
   rename of stored `body` with no way back) as Critical (Decided 3).
   Its counts are recorded beside the panel's `1 C · 11 I · 2 M` on the same
   fixture, with its cost line and whether it also flags the hard-coded
   `notes.json` against README's `NOTES_PATH`.
2. Withdrawn with FR5 (Decided 7).
3. `python3 -B tests/skills/spec/test_spec.py` is green with the new pins;
   SKILL.md stays at most 24,000 bytes.
```

## 4.3 Functional Requirements

FR1: a light run covers a local stored-data change
- **Input**: a `/spec light` run, or a light offer, for a feature in one area
  of the code, about five plan tasks at most.
- **Processing**: the Light rule drops "no schema or stored-data change"; it
  excludes only a feature touching auth, secrets, user data or data that
  leaves the machine. **User data** = accounts, personal data about people,
  or content other people can see or send — not the project's own state,
  config, logs or check records, nor the owner's own local files (the toy
  fixture's local `notes.json` is on the light side). **Leaves the machine**
  = sent over the network or to a third-party service (a git push of the
  project's own repo excepted). A light run writes each companion it
  triggers as its spec section, always inside the spec: data and migration
  with rollback (4.4 and 4.12), the API contract (4.7), spike notes (4.12,
  each spike a first plan task); Step 4.2's companion rule says so for light
  mode. Only the threat model's trigger appearing mid-run switches Steps 4
  onward to full, said in one line with the added cost (the existing
  notice).
- **Output**: the light spec carries the data and migration section with its
  rollback; Step 5 stays one reviewer.

FR2: the threat model's trigger names data that leaves the machine
- **Processing**: the companions table's threat-model trigger reads "auth,
  secrets, user data or data that leaves the machine", the same set that
  switches a light run to full.

FR3: the single reviewer checks the rollback
- **Processing**: § Checks in `references/review.md` gains the row "every
  change to stored data or a public interface names its consumers and its
  rollback (a down() for each up())" — group Completeness, role claims
  against the code (it reads the code, so it can check the consumers named
  are all of them). The single reviewer gets it with the whole table.

FR4: light round 2 after a Critical stored-data fix (Decided 5)
- **Processing**: `references/review.md` § Round 2: a light run has no round
  2, except when round 1 fixed a Critical finding on stored data or a public
  interface — then ONE fresh reviewer, as § Round 2 says.

FR5: withdrawn (Decided 7) — every go with changes keeps its one reviewer
round; no removal-only path.

FR6: pins
- **Processing**: `tests/skills/spec/test_spec.py` pins FR1–FR4's wording
  and asserts the Light rule no longer holds "no schema or stored-data
  change", "and no companions" or "A companion trigger appearing mid-run",
  the companions table no longer holds "| auth, secrets or user data |", and
  neither SKILL.md nor review.md holds "removal-only".

## 4.6 Technical Architecture

Rule edits only, no code: SKILL.md § Invocation (Light), Step 4.2 (the
light-mode note and the threat-model trigger) and Step 6 (the light-mode
`fixed — not re-reviewed` note); `references/review.md` — § Checks (one row)
and § Round 2 (the light exception). SKILL.md stays under its byte cap.

## Alternatives considered

| approach | why not |
|---|---|
| keep the switch for every companion trigger | the cost this cut removes; FR3's row and FR4's round 2 keep what the panel caught on stored data |
| a mechanical grep in place of the reviewer on a go with changes that only drops items (built as FR5, then withdrawn) | three reviews found 16 Important gaps in it — the judgement a reviewer gives, which a grep cannot; it saved one ~65k–110k round on a rare go |
| a panel-vs-single A/B on two fixtures before the cut | stronger evidence, ~500k tokens; one measured single run against the panel's recorded counts answers the question that matters (criterion 1) |

## 4.8 Edge Cases & Errors

- A light run whose stored-data change also sends data off the machine →
  the threat-model trigger wins: switch to full.
- The single reviewer misses the seeded rollback as Critical (criterion 1
  fails) → `/dev` stops before FR1, FR2 and FR4 are written; only the FR3
  row is committed.

## 4.10 Testing Strategy

Wording pins in `test_spec.py`, written first (fail before the edit),
including pins that the old Light text is gone. One measured reviewer run on
the seeded fixture, before the rule change it gates (criterion 1).

## 4.11 Implementation Roadmap

`docs/plan/review-cut.md`.

## 4.12 Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| one reviewer misses a stored-data gap a panel would catch | Medium | High | FR3's row; criterion 1 measured at the panel's bar, before the switch changes |
| only the rollback seed gates criterion 1 | Medium | Low | the `NOTES_PATH` catch is recorded beside it; the panel run kept no list to compare it with |
| SKILL.md passes 24,000 bytes | Low | Low | `test_skill_size` |

## 4.13 Out of Scope

- Idea 3 of the cut (fewer panel roles); only after a `/tune` A/B.
- The full-mode panels and `/rev`'s review tiers.

## Decided

1. A local stored-data change keeps its data and migration section with
   rollback in a light spec; the review stays one reviewer (owner 31Oct26).
2. A removal-only go with changes gets a mechanical dangling-reference grep
   instead of a reviewer (owner 31Oct26) — reversed by Decided 7.
3. Quality is measured by one single-reviewer run on the seeded toy fixture;
   the bar is the missing rollback flagged as Critical or Important (owner
   31Oct26); at the go the bar became Critical, the panel's own grade for
   this seed (owner 31Oct26).
4. The light→full switch fires only for auth, secrets, user data or data
   that leaves the machine (owner, idea 1).
5. A light run gets round 2 (one reviewer) after round 1 fixed a Critical
   finding on stored data or a public interface (owner 31Oct26, at the go).
6. The removal-only path is for new features only, and only for an FR, an
   Assumption, a plan task or a To file entry touching no security, stored
   data or interface (owner 31Oct26, at the go) — reversed by Decided 7.
7. The removal-only path is removed: every go with changes keeps its one
   reviewer round; FR5 and criterion 2 are withdrawn (owner 31Oct26, at
   /rev, after three reviews found 16 Important gaps in it).

## Assumptions

- The API-contract and spike companions, like the data one, stay light and
  are written as spec sections (Decided 4 names the only switch triggers).
- The threat-model trigger gains "data that leaves the machine", so the
  switch set and the companion that justifies it are the same set (FR2).
- Approach: rule edits in SKILL.md and review.md, pinned by `test_spec.py`.

## Prerequisites

None.

## To file

- **reqs** (`skills/spec/docs/reqs.md`, § Review): A light run takes a local
  schema or stored-data change and writes its data and migration section,
  with rollback, inside the spec; one reviewer checks that every change to
  stored data or a public interface names its consumers and its rollback,
  and a Critical fix there gets round 2. Only auth, secrets, user data
  (accounts, personal data, content others see) or data that leaves the
  machine switches a light run to full. Spec: `docs/spec/review-cut.md`.
- **arch**: none (the removal-only decision line and Flow edges were filed,
  then removed with Decided 7).
- **tasks** (`skills/spec/docs/tasks.md`): Build review-cut —
  docs/plan/review-cut.md; and "Fewer review-panel roles — only after a
  `/tune` A/B" (Out of Scope, for future consideration).

## Review

`single review: 1 agent · 155k tokens · 5 min` — light mode, one round:
0 Critical · 13 Important · 9 Minor; 10 Important and 9 Minor fixed — not
re-reviewed; 3 Important went to the go as Open questions (they changed
scope or Decided 3) and were settled there as Decided 3, 5 and 6. Write check: matched before and after (`4fd0ea0…`).

| # | sev | finding | outcome |
|---|---|---|---|
| 1 | Important | criterion 1's "Critical or Important" bar is below the panel's recorded Critical, the bar that rejected `sonnet` roles | Decided 3 (go) |
| 2 | Important | the measurement mainly tests that the new row is read; no-plan rows, seed hints and the `NOTES_PATH` seed unaddressed | fixed — not re-reviewed: criterion 1 skips plan-only rows, names no seed, records `NOTES_PATH` and the panel's counts; 4.12 row |
| 3 | Important | the gate (criterion 1) ran after FR1/FR2 were committed | fixed — not re-reviewed: plan measures right after the FR3 row, before FR1, FR2 and FR4 |
| 4 | Important | "user data" and "leaves the machine" undefined; the fixture itself ambiguous | fixed — not re-reviewed: both defined in FR1, fixture placed on the light side |
| 5 | Important | bare-id grep misses ranges ("FR4–FR6"); FR4 matches FR40; criterion 2's FR unnamed | fixed — not re-reviewed: word-bounded ids, range patterns, a range hit ends the path; criterion 2 drops FR5 |
| 6 | Important | items without an id or title (decision, criterion, section) are never searched | fixed — not re-reviewed: FR5 now takes only FRs, Assumptions, tasks and To file entries, each with its id form (with #9) |
| 7 | Important | deleting hits falsifies Review and Decided; the drop is never recorded | fixed — not re-reviewed: Review hits kept, Decided/Alternatives hit ends the path, drop recorded in Decided |
| 8 | Important | conflicts with re-runs (spec-only plan read-only; `(planned)` drop entries) | Decided 6 (go): new features only |
| 9 | Important | a removal can open a gap no reference shows (companion, error path, criterion, security) | Decided 6 (go): narrowed kinds |
| 10 | Important | a stored-data Critical fix in light mode loses round 2 | Decided 5 (go): FR4 |
| 11 | Important | pins let the old "no companions" and switch sentence survive | fixed — not re-reviewed: FR6 negative pins |
| 12 | Important | Mermaid id `G` clashes with the concept gate | fixed — not re-reviewed: `RM` |
| 13 | Important | `0 hits` is silence-means-pass | fixed — not re-reviewed: grep before deleting, each term must hit its definition, before/after counts |
| 14 | Minor | the switch rewrite may drop the pinned "said in one line with the added cost" | fixed — not re-reviewed: FR1 and plan keep it word for word |
| 15 | Minor | Step 4.2's "own file beyond one screen" contradicts light's inside-the-spec | fixed — not re-reviewed: Step 4.2 light-mode note |
| 16 | Minor | FR3's role (design critic) cannot read the code for consumers | fixed — not re-reviewed: role claims against the code |
| 17 | Minor | dropping a task always changes the Estimate | fixed — not re-reviewed: Estimate recomputed as part of the path |
| 18 | Minor | walk set and `pending — walk` marks unstated for the path | fixed — not re-reviewed: FR5 step 4 |
| 19 | Minor | review.md's READ line misses the path | fixed — not re-reviewed: 4.6 lists the READ line edit |
| 20 | Minor | § Cap and cost does not name the new Review line | fixed — not re-reviewed: 4.6 lists it, no dispatch |
| 21 | Minor | the no-renumber rule missing from reqs To file | fixed — not re-reviewed |
| 22 | Minor | after a rewording hit, writing-plans' re-invocation unstated | fixed — not re-reviewed: re-invoked with the deletions as the change |

**Acceptance**

| # | criterion | result |
|---|---|---|
| 1 | one light reviewer on `toy/seeded-spec.md` (no plan, no seed named, § Checks with the Task 1 row) flags the missing rollback as Critical | ✅ `single review: 1 agent · 102k tokens · 1 min` — 1 C · 10 I · 3 M against the panel's 1 C · 11 I · 2 M; the rollback Critical (no down(), truncating write, revert breaks `list_notes`); `NOTES_PATH` vs hard-coded `notes.json` flagged as Minor |
| 2 | dropping FR5 from scratch copies of check-reuse's spec and plan finds every reference, ranges included | – withdrawn (Decided 7); the run before it: the final § Removal-only change grep: 8 reference lines (id hits incl. the definition row `spec.md:77`; ranges "FR4–FR5" `:45`, "FR4–FR6" `:206`; list "FR5, FR6" in Review `:253`); a looser read found 0 more; one date match (`:281` "Task 4, 2026-10-30") rejected by the read step. The ranges and `plan.md:72` (needs rewording) end the path, so it goes to the reviewer round, as intended; the delete-and-re-grep half ran in no sample here |
| 3 | `test_spec.py` green, SKILL.md ≤ 24,000 bytes | ✅ 19 tests OK; SKILL.md 22,419 bytes |

**Build review** (dev, small tier): Task 3 0 C · 1 I · 5 M, the Important fixed and test-pinned; Task 4 round 1 0 C · 7 I · 8 M, fixed; round 2 0 C · 3 I · 9 M — fixed after round 2, not re-reviewed (id lists, entries that serve only the dropped item, a task that is a kept FR's only coverage).

**Rev** (base `1be466c`, round 1): 0 C · 7 I · 9 M. I7, M5, M6 and M9 fixed in `1ab04e8`; I1–I6 and M1–M4, M7 and M8 all lay in the removal-only path — moot, as the path was removed (Decided 7).
