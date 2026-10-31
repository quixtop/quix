# think-lenient Implementation Plan
Status: approved 2026-10-31

> **For agentic workers:** execute with `/dev` (it commits each task and keeps
> its ledger). Steps use checkbox (`- [ ]`) syntax. Commits go through a
> Terminal-panel tab (Bash cannot write `~/.agents/.git`), named files only;
> never push.

**Goal:** the full-mode think stage stops at the concept gate only for a
required-topic inference or a contradiction, runs only the triggered idea
lenses, and asks for the approach only on a scope or security difference.

**Architecture:** rule edits in `skills/spec/references/lenses.md` (a
**Runs** line per idea lens), `references/think.md` (intro, § Concept gate,
§ Idea panel, § Approach pick), `references/review.md` § Cap and cost and
SKILL.md's Quick Reference row 3, each pinned by wording tests in
`test_spec.py`; one headless measured run proves the result.

**Tech Stack:** Markdown skill files; Python `unittest` (`test_spec.py`);
`claude -p` for the headless run.

**Spec:** `skills/spec/docs/spec/think-lenient.md`

**Estimate:** about 1.75 h in all (Task 1: 15 min; Task 2: 35 min; Task 3:
15 min; Task 4: 35 min and one headless run, ~$2–6 of session usage).

## Global Constraints

- SKILL.md stays under 24,000 bytes (`Baseline.test_skill_size`; 22,315 now).
- The always-lenses are exactly Scope and reuse and Pre-mortem.
- The gate's stop rows are exactly the drill's required-topic rows 1, 2, 4, 5
  and 6 (not every row the bank marks CRITICAL: row 3 is not one).
- The planned-spend line is exactly `idea panel: <n> agents · ~<k>k tokens ·
  skipped: <lens> (<reason>), …`; `<k>` is about 56 per agent.
- The question drill (think.md § Drill) is not edited.
- The extra wave of named skipped lenses is spec Decided 6.

## Review Focus

1. A concept that triggers no optional lens → the two always-lenses and the
   merger run (Task 2 pins "the two always-lenses").
2. A trigger the run is unsure of → the lens runs (Task 2 pins "counts as
   holding").
3. A found Assumption on a required-topic row → the gate stops and names the
   rows (Task 2 pins "naming those rows").
4. A STOP recovery → re-runs only lenses that ran (Task 2 pins "only lenses
   that ran").
5. A lens agent judging its own trigger → its brief leaves the **Runs** line
   out (Task 1 pins "without its **Runs** line").

---

### Task 1: A Runs line on every idea lens (FR1)

**Files:**
- Modify: `skills/spec/references/lenses.md` — § Idea lenses, one `**Runs**:`
  line after **Reads** per lens (a lens is defined in one place); the intro's
  "word for word" sentence and § Idea lenses' "confirmed concept": the brief
  must leave **Runs** out and the gate may not confirm.
- Test: `tests/skills/spec/test_spec.py` — `Lenses.test_lenses_shape`.

**Interfaces:**
- Produces: the label `**Runs**:`, which Task 2's § Idea panel reads.

- [ ] **Step 1: Failing test** — in `test_lenses_shape`: every idea lens's
  fifth label is `**Runs**:` and no review role has one; the Runs line holds,
  per lens:

  | lens | needle |
  |---|---|
  | scope and reuse | starts with "Always" |
  | cost and limits | "calls agents, APIs or the network" |
  | ease of use | "a flow a person uses" |
  | migration and rollback | "stored data or a public interface changes" |
  | monitoring | "runs unattended" |
  | upkeep | "adds files or dependencies" |
  | pre-mortem | starts with "Always" |

  and exactly those two start with "Always". The intro holds "without its
  **Runs** line"; § Idea lenses holds "the concept the gate passed" and not
  "the confirmed concept".
- [ ] **Step 2: Run** `python3 -B ~/.agents/tests/skills/spec/test_spec.py`
  → FAIL in `test_lenses_shape`.
- [ ] **Step 3: Edit** with spec FR1's wording.
- [ ] **Step 4: Run** → 19 tests OK.
- [ ] **Step 5: Commit** `lenses.md`, `test_spec.py`.

**Done when:** `test_lenses_shape` passes with a Runs line on all 7 idea
lenses and none on the review roles.

### Task 2: The think stage asks less (FR2 run rule, FR3, FR4, FR5 intro)

**Files:**
- Modify: `skills/spec/references/think.md` — the intro's turn list, § Concept
  gate, § Idea panel, § Approach pick: the think stage's rules live here.
- Test: `tests/skills/spec/test_spec.py` — `Think.test_think_rules`.

**Interfaces:**
- Consumes: Task 1's `**Runs**:` label.

- [ ] **Step 1: Failing tests.** In `test_think_rules`:
  - intro: keep "a lens STOP (`references/review.md` § Panel)"; add "the
    concept gate when it stops" and "the approach pick when approaches
    differ on scope or security";
  - § Concept gate — replace "No agent runs before the confirm" with "No
    agent runs before the gate goes on or is confirmed"; replace "found in
    the request or the code — Decided at the confirm" with "found in the
    request or the code — Decided if you confirm at a stop, else
    Assumptions until the go" and assert "Decided at the confirm" absent;
    replace "The confirm moves the first group into Decided" with "at a
    stop, a confirm moves the found group into Decided"; keep "Assumptions
    in two labelled groups" and "recommended answers — stay Assumptions; the
    go approves them"; add "only when an Assumption found in the request or
    the code answers one of the drill's required-topic rows", "1, 2, 4, 5 or
    6", "naming those rows", "otherwise it goes on in the same turn", "The
    gate decides when found Assumptions move";
  - § Idea panel — add "whose **Runs** line holds", "the concept the gate
    passed", "no cap", "counts as holding", "the two always-lenses", "No lens
    is stopped early", "named with its one-line reason", "only lenses that
    ran", "the triggered lenses only", "ONE extra wave plus a merger",
    "inside the cap of 8", "runs no other second time"; assert "the 7 idea
    lenses" and "never runs a second time" absent (replace that pin);
  - § Approach pick — keep "the user picks, and the pick is **Decided**";
    replace "scope, security, cost or user flow" with "differ in scope or
    security" and "cost or user flow included", and assert the old phrase
    absent.
- [ ] **Step 2: Run** → FAIL in `test_think_rules`.
- [ ] **Step 3: Edit** per spec FR2 (the run rule, the extra wave and edge
  cases 1, 6), FR3, FR4 and FR5's intro list; § Drill is not touched.
- [ ] **Step 4: Run** → 19 tests OK.
- [ ] **Step 5: Commit** `think.md`, `test_spec.py`.

**Done when:** `test_think_rules` passes, its negative pins included.

### Task 3: The cost lines and the Quick Reference (FR2 output, FR5)

**Files:**
- Modify: `skills/spec/references/review.md` — § Cap and cost's dispatch
  plan, planned-spend line and the idea panel's Review cost line: review.md
  owns the cost lines.
- Modify: `skills/spec/SKILL.md` — Quick Reference row 3: the one-line map of
  the steps.
- Test: `tests/skills/spec/test_spec.py` — `Review.test_review_rules` (the
  Cap and cost pins and the cap-sum check), `Modes.test_modes`.

- [ ] **Step 1: Failing tests** — Cap and cost holds "the idea panel at most
  8 (up to 7 lenses, 1 merger, an extra wave of named skipped lenses
  included)" in place of "the idea panel 8 (7 lenses, 1 merger)";
  "`idea panel: <n> agents · ~<k>k tokens · skipped: <lens> (<reason>), …`"
  and "about 56 per agent" in place of "idea panel: 8 agents · ~450k tokens"
  (now a negative pin); and "· skipped:" in the Review cost-line paragraph.
  The cap-sum regex becomes `panel (?:at most )?(\d+) \(|round 2 (\d+)`, its
  sum still 15. SKILL.md holds "idea panel (triggered lenses), you pick on a
  scope or security difference, save point".
- [ ] **Step 2: Run** → FAIL in those tests.
- [ ] **Step 3: Edit** both files; keep "plan at most 15 dispatches" and
  "review panel: 6 agents · ~330k–450k tokens" word for word.
- [ ] **Step 4: Run** → 19 tests OK; `test_skill_size` passes.
- [ ] **Step 5: Commit** `review.md`, `SKILL.md`, `test_spec.py`.

**Done when:** the pins pass and SKILL.md is under 24,000 bytes.

### Task 4: Acceptance — the A/B think sample, suite green (criteria 1, 2)

**Files:**
- Modify: `skills/spec/docs/spec/think-lenient.md` § Review — an "Acceptance"
  table: the spec records its own proof.

- [ ] **Step 1:** write the expected run/skip set into the Acceptance table
  BEFORE the run (spec criterion 1: run Scope and reuse, Pre-mortem,
  Migration, Ease of use, Upkeep; skip Cost and limits, Monitoring).
- [ ] **Step 2 (criterion 1):** in a Terminal-panel tab, copy
  `tests/skills/spec/fixtures/toy` into a throwaway git repo under the
  scratchpad, install the edited skill there as a project skill, and run
  `claude -p "/spec think add tags to notes; the plugin system for future
  tag types is a must-have" --output-format json` turn by turn with
  `--continue`. `--allowedTools` is the Phase 5 list of
  `docs/spec/think-and-review-spikes.md` (Task 1's list plus `Bash(git
  diff:*)`, `Bash(git ls-files:*)` and the `checks.sh fp` command) plus
  `Edit(//<scratchpad>/**)` and `Write(//<scratchpad>/**)`, so panel files
  and the write check run as in the A/B. Answer "recommended for the rest"
  at the drill, "confirm" if the gate stops, the recommended pick if asked;
  stop at the save point.
- [ ] **Step 3:** record: lenses run and skipped with reasons, against the
  expected set; whether the gate stopped and why; whether the plugin
  contract was challenged; the panel's own cost line, and the turn's
  `total_cost_usd` with what that turn included, beside the A/B's
  panel-only $2.34. Remove the throwaway repo.
- [ ] **Step 4:** the plugin contract not challenged, or Scope and reuse
  not run → **STOP**: report it, commit nothing further. A run/skip set
  that differs from the expected one is recorded and reported, not a stop.
- [ ] **Step 5 (criterion 2):** `python3 -B
  ~/.agents/tests/skills/spec/test_spec.py` → OK (19 tests).
- [ ] **Step 6:** write the Acceptance rows; commit the spec.

**Done when:** criteria 1 and 2 are ✅ in the spec's Review and the suite is
green on the final tree.
