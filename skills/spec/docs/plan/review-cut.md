# review-cut Implementation Plan
Status: approved 2026-10-31 · built 2026-10-31 (Tasks 1–5) · Task 4 and Task 5
Step 1 withdrawn at /rev: the removal-only path was removed (spec Decided 7)

> **For agentic workers:** execute with `/dev` (it commits each task and keeps
> its ledger). Steps use checkbox (`- [ ]`) syntax. Commits go through a
> Terminal-panel tab (Bash cannot write `~/.agents/.git`), named files only;
> never push.

**Goal:** a light run keeps a local stored-data change on one reviewer that
checks its rollback, and a removal-only go with changes is checked by a grep
instead of a reviewer.

**Architecture:** rule edits in `skills/spec/SKILL.md` (Light, Step 4.2,
a Step 6 pointer) and `skills/spec/references/review.md` (READ line, one
Checks row, § Round 2, § Cap and cost, a new § Removal-only change after
§ Walk at the go), each pinned by wording tests in `test_spec.py`. The
measurement that gates the Light change runs right after the Checks row it
measures, before the Light change is written.

**Tech Stack:** Markdown skill files; Python `unittest` (`test_spec.py`);
one `general-purpose` reviewer subagent for the measurement.

**Spec:** `skills/spec/docs/spec/review-cut.md`

**Estimate:** about 1.5 h in all (Task 1: 10 min; Task 2: 15 min and
~65k–155k reviewer tokens; Task 3: 25 min; Task 4: 25 min; Task 5: 15 min).

## Global Constraints

- SKILL.md stays under 24,000 bytes (`Baseline.test_skill_size`; 21,694 now).
- The switch set is exactly "auth, secrets, user data or data that leaves the
  machine", in the Light rule and in the threat-model trigger.
- "said in one line with the added cost", "in place of one reviewer (~65k)"
  and "Light mode has no round 2" stay word for word (existing pins).
- The Review line is exactly `go-with-changes: removal-only · <t> terms ·
  <h> hits before · <r> left after · 0 agents`.

## Review Focus

1. A stored-data change that also sends data off the machine → full mode
   (Task 3 pins "Only the threat model's trigger").
2. A removal mixed with any other change, or of an unlisted kind → the
   normal round (Task 4 pins "adds or rewords nothing else").
3. A dropped id inside a range ("FR4–FR6") → ends the path (Task 4 pins
   "every range"; Task 5 drops FR5 of check-reuse).
4. A term that hits not even its own definition line → never recorded as
   `0 hits` (Task 4 pins "its own definition line").
5. A hit in Review → kept; in Decided or Alternatives → the reviewer round
   (Task 4 pins "Hits in Review are kept").

---

### Task 1: The rollback row in § Checks (FR3)

**Files:**
- Modify: `skills/spec/references/review.md` — one § Checks row after
  "every triggered companion present": the single reviewer's brief is that
  table.
- Test: `tests/skills/spec/test_spec.py` — `Review.test_checks_table`.

- [ ] **Step 1: Failing test** — counts 28 → 29, and add the owner pair
  `("every change to stored data or a public interface names its consumers
  and its rollback (a down() for each up())", "claims against the code")`.
- [ ] **Step 2: Run** `python3 -B ~/.agents/tests/skills/spec/test_spec.py`
  → FAIL in `test_checks_table`.
- [ ] **Step 3: Add the row** — group Completeness, role claims against the
  code.
- [ ] **Step 4: Run** → 18 tests OK.
- [ ] **Step 5: Commit** `review.md`, `test_spec.py`.

**Done when:** `test_checks_table` passes with 29 rows.

### Task 2: Gate — measured single reviewer (criterion 1)

**Files:**
- Modify: `skills/spec/docs/spec/review-cut.md` § Review — an "Acceptance"
  table, criterion 1's row: the spec records its own proof.

- [ ] **Step 1:** dispatch ONE `general-purpose` reviewer on the session
  model, briefed as § Single reviewer says for light mode (the reviewer
  brief lines, the lenses.md "Every agent" list, § Checks as built by Task
  1), over `tests/skills/spec/fixtures/toy/seeded-spec.md`, `<root>` =
  `tests/skills/spec/fixtures/toy`; told there is no plan, and to skip the
  plan-only rows § Standalone review lists. The brief names no seed and
  hints at none.
- [ ] **Step 2:** record its counts beside the panel's `1 C · 11 I · 2 M`,
  its `single review:` cost line, the severity it gives the missing
  rollback, and whether it flags the hard-coded `notes.json` against
  README's `NOTES_PATH`.
- [ ] **Step 3:** the rollback is Critical → commit the spec, go on.
  Otherwise **STOP** the run (a gate that cannot be made green): Tasks 3–5
  are not run, FR1, FR2 and FR4 are not written, and the report names the
  result.

**Done when:** the rollback is flagged Critical, recorded in the spec.

### Task 3: Light covers a local stored-data change (FR1, FR2, FR4)

**Files:**
- Modify: `skills/spec/SKILL.md` — § Invocation's **Light** bullet, Step
  4.2's companion rule (light mode: always inside the spec) and its
  threat-model trigger: where the switch rule and the triggers live.
- Modify: `skills/spec/references/review.md` — § Round 2's light exception
  (FR4).
- Test: `tests/skills/spec/test_spec.py` — `Modes.test_modes`,
  `Review.test_review_rules`.

- [ ] **Step 1: Failing tests.** In `Modes.test_modes`, the light pins
  become `["offered on the drill's first turn", "about five plan tasks at
  most", "nothing touching auth, secrets, user data or data that leaves the
  machine", "content other people can see or send", "sent over the network
  or to a third-party service", "always inside the spec", "data and
  migration with rollback", "Only the threat model's trigger"]`, plus
  `assertNotIn` for "no schema or stored-data change", "and no companions"
  and "A companion trigger appearing mid-run" on `flat(light[0])`; on
  SKILL.md, `"| auth, secrets, user data or data that leaves the machine |"`
  present, `"| auth, secrets or user data |"` absent, and "(light mode:
  always inside the spec)" in Step 4. In `Review.test_review_rules`, § Round
  2 also holds "except when round 1 fixed a Critical finding on stored data
  or a public interface".
- [ ] **Step 2: Run** → FAIL in `test_modes` and `test_review_rules`.
- [ ] **Step 3: Edit** per spec FR1 (with both definitions), FR2 and FR4,
  keeping the Global Constraints phrases.
- [ ] **Step 4: Run** → 18 tests OK; `test_skill_size` passes.
- [ ] **Step 5: Commit** `SKILL.md`, `review.md`, `test_spec.py`.

**Done when:** both tests pass and SKILL.md is under 24,000 bytes.

### Task 4: Removal-only go with changes (FR5)

**Files:**
- Modify: `skills/spec/references/review.md` — a new § Removal-only change
  after § Walk at the go (review.md owns the go-with-changes rounds); its
  READ line names the path; § Cap and cost names the Review line and that it
  makes no dispatch.
- Modify: `skills/spec/SKILL.md` — Step 6's **Go with changes** bullet gains
  one pointer sentence: the go is where the user meets it.
- Test: `tests/skills/spec/test_spec.py` — new `Review.test_removal_only`;
  the Step 6 pin in `Modes.test_modes`.

**Interfaces:**
- Produces: the heading `## Removal-only change`, which the Step 6 pointer
  names.

- [ ] **Step 1: Failing test** — in class `Review`:

```python
def test_removal_only(self):
    text = REVIEW.read_text()
    rem = section(text, "## Removal-only change")
    self.has_all(rem, [
        "a new feature's go with changes", "an FR, an Assumption, a plan task",
        "none touching security, stored data or an interface",
        "adds or rewords nothing else", "A re-run", "Before deleting",
        "`\\bFR<n>\\b`", "every range", "its own definition line", "`file:line`",
        "writing-plans is not re-invoked", "nothing is renumbered",
        "Estimate is recomputed", "`dropped FR<n> — owner <date>`",
        "Hits in Review are kept", "in Decided or Alternatives",
        "needs rewording, not deletion", "the normal go-with-changes round",
        "with the deletions as the change", "`pending — walk`",
        "with the full Step 6 block",
        "go-with-changes: removal-only · <t> terms · <h> hits before · <r> left after · 0 agents"])
    self.has_all(section(text, "## Cap and cost"), ["removal-only", "no dispatch"])
```

  and add `"`references/review.md` § Removal-only change"` to the Step 6
  pin list.
- [ ] **Step 2: Run** → FAIL in `test_removal_only` (section missing).
- [ ] **Step 3: Write § Removal-only change** from spec FR5 and § 4.8 using
  each pinned phrase; add the READ-line mention (keeping "at Step 6's
  walk"), the Cap and cost sentence, and the Step 6 pointer: "A change that
  only drops items takes `references/review.md` § Removal-only change
  instead of the round."
- [ ] **Step 4: Run** → 19 tests OK; `test_skill_size` passes.
- [ ] **Step 5: Commit** `review.md`, `SKILL.md`, `test_spec.py`.

**Done when:** `test_removal_only` passes and the suite is green.

### Task 5: Acceptance — removal exercise, suite green (criteria 2, 3)

**Files:**
- Modify: `skills/spec/docs/spec/review-cut.md` § Review — the Acceptance
  table's rows 2 and 3.

- [ ] **Step 1 (criterion 2):** copy `skills/_shared/docs/spec/check-reuse.md`
  and `skills/_shared/docs/plan/check-reuse.md` into the scratchpad; drop
  FR5 there by § Removal-only change; compare its hit list with a read of
  both copies (the ranges "FR4–FR5" and "FR4–FR6" must be hits that end the
  path); record hits, left after, and any reference the grep missed (must
  be 0).
- [ ] **Step 2 (criterion 3):** `python3 -B ~/.agents/tests/skills/spec/test_spec.py`
  → OK (19 tests).
- [ ] **Step 3:** write rows 2 and 3; remove the scratch copies; commit the
  spec.

**Done when:** criteria 1–3 are ✅ in the spec's Review and the suite is
green on the final tree.
