# go-walkthrough Implementation Plan
Status: approved 2026-10-28 · built 2026-10-28 (Tasks 1–2 in one commit, they share the test file)

> **For agentic workers:** execute with `/dev` (it commits each task and keeps
> its ledger). Steps use checkbox (`- [ ]`) syntax. Commits go through a
> Terminal-panel tab (Bash cannot write `~/.agents/.git`), named files only.

**Goal:** at Step 6's go, "walk" takes the review findings one per turn and
applies the changes as ONE go-with-changes round.

**Architecture:** the walk's procedure is a new § Walk at the go in
`references/review.md`, after § Closing findings; SKILL.md Step 6 names
"walk" in the go question and points there. Both are pinned by wording
tests.

**Tech Stack:** Markdown skill files; Python `unittest` (`test_spec.py`);
`claude -p --continue` for the proving run.

**Spec:** `skills/spec/docs/spec/go-walkthrough.md`

**Estimate:** about 1.5 h in all (Tasks 1–2: 30 min; Task 3: 45 min of
headless turns, about $3; Task 4: 10 min).

## Global Constraints

- SKILL.md stays under 24,000 bytes (`Baseline.test_skill_size`).
- The four answers are exactly `keep` · `change <how>` · `to tasks` · `stop`.
- The Review line is exactly
  `walk: <n> findings · kept <k> · changed <c> · to tasks <t>`.
- A plain go, go with changes, no-go and drop it are unchanged.

## Review Focus

1. "walk" with an empty walk set → "nothing to walk", the go asked again
   (Task 1 test pins "nothing to walk").
2. "go" typed mid-walk → read as `stop`; collected changes still run their
   round first (Task 1 test pins "read as `stop`").
3. An unknown reply → the same finding again, with the four answers (Task 1
   test pins "shown again").
4. `to tasks` on an open Critical → allowed; its Review entry reads
   `to tasks — deferred` (Task 1 test pins it).
5. A change round that raises new findings → the next walk covers only that
   round's new findings (Task 1 test pins "only that round's new findings").

---

### Task 1: § Walk at the go in review.md

**Files:**
- Modify: `skills/spec/references/review.md` — add § Walk at the go after
  § Closing findings: the procedure lives beside the findings it walks.
- Test: `tests/skills/spec/test_spec.py` — `Review.test_walk`, pins FR2–FR5
  and the Review Focus lines.

**Interfaces:**
- Produces: the heading `## Walk at the go`, which Task 2's SKILL.md
  pointer names.

- [ ] **Step 1: Write the failing test** — in class `Review`:

```python
def test_walk(self):
    walk = section(REVIEW.read_text(), "## Walk at the go")
    self.has_all(walk, [
        "Critical findings still open", "`fixed after round 2 — not re-reviewed`",
        "light mode's `fixed — not re-reviewed`", "round-1 fixes that stood on round 1",
        "a go-with-changes round's fixes", "Important findings logged open after round 2",
        "logged Minor findings", "a refutation on the record are not walked",
        "`Finding <i>/<n> · <severity> · <file or section>`",
        "`keep` · `change <how>` · `to tasks` · `stop`", "`pending — walk`",
        "`(from walk — not reviewed)`", "`to tasks — deferred`", "shown again",
        "the entry never takes a `provisional` mark", "re-review the fix for <finding>",
        "reply `change <how>` to record it",
        "read as `stop`", "a mid-walk go is never the go",
        "go-with-changes path, once", "with the full Step 6 block",
        "only that round's new findings", "nothing to walk",
        "walk: <n> findings · kept <k> · changed <c> · to tasks <t>"])
```

(`REVIEW` is already defined at `test_spec.py:20`.)

- [ ] **Step 2: Run it** — `python3 -B ~/.agents/tests/skills/spec/test_spec.py`
  → FAIL in `test_walk` (section missing).
- [ ] **Step 3: Write § Walk at the go** from the spec's FR2–FR5, § 4.8 and
  § 4.12, using each pinned phrase.
- [ ] **Step 4: Run it** → 18 tests OK.
- [ ] **Step 5: Commit** `review.md`, `test_spec.py`.

**Done when:** `test_walk` passes and the suite is green.

### Task 2: SKILL.md Step 6 names the walk

**Files:**
- Modify: `skills/spec/SKILL.md` — Step 6's ask names "walk"; one **Walk**
  bullet points to `references/review.md` § Walk at the go: the go is where
  the user meets it.
- Test: `tests/skills/spec/test_spec.py` — extend the `Modes` Step 6 line.

**Interfaces:**
- Consumes: the `## Walk at the go` heading (Task 1).

- [ ] **Step 1: Write the failing test** — replace
  `self.has_all(section(text, "## Step 6"), ["reviewer brief"])` with
  `["reviewer brief", "drop it or walk (when", "**Walk** →", "`references/review.md` § Walk at the go"]`.
- [ ] **Step 2: Run it** → FAIL on "drop it or walk (when".
- [ ] **Step 3: Edit Step 6**: the ask becomes "ASK for go, go with changes,
  no-go, drop it or walk (when the walk set of `references/review.md` § Walk
  at the go is not empty)", and add, after **Go with changes**: "**Walk** →
  READ `references/review.md` § Walk at the go and run it; it ends at this
  question again."
- [ ] **Step 4: Run it** → OK; `Baseline.test_skill_size` still passes.
- [ ] **Step 5: Commit** `SKILL.md`, `test_spec.py`.

**Done when:** the Step 6 test passes and SKILL.md is under 24,000 bytes.

### Task 3: Acceptance — headless proving run

**Files:**
- Modify: `skills/spec/docs/spec/go-walkthrough.md` § Review — one "Proving
  run" line per check: the spec records its own acceptance.

- [ ] **Step 1:** Copy `tests/skills/spec/fixtures/toy/` into a throwaway git
  repo under the session scratchpad; with the spikes' `--allowedTools` list
  (plus `Edit(//<scratchpad>/**)`), run `/spec light add a purge-old-notes
  command` (no error path stated, so the reviewer finds one) turn by turn
  until the go. The walk set is empty → re-run with a vaguer request.
- [ ] **Step 2:** Answer "walk": check one finding per turn, in the walk
  order; answer `change <how>` once, `keep` for the rest.
- [ ] **Step 3:** Check that ONE go-with-changes round ran and the go was asked
  again, with the `walk:` line in the Review section.
- [ ] **Step 4:** In a second fixture, answer a plain "go": the filing runs at
  once with no walk.
- [ ] **Step 5:** Record both results; remove the fixtures; commit the spec.

**Done when:** both checks are ✅ in the spec's Review, and no fixture or
`claude -p` process is left.

### Task 4: Acceptance — suite green

- [ ] **Step 1:** `python3 -B ~/.agents/tests/skills/spec/test_spec.py` → OK
  (18 tests).

**Done when:** the suite is green on the final tree.
