# think-and-review Implementation Plan
Status: approved 2026-10-27 · built 2026-10-28 (commits 1380092–56f2075, then the /rev fixes); test and section names below are as planned — the suite and references were restructured by the /rev (see the spec's § Review, "As built")

> **For agentic workers:** execute with `/dev` (it commits each task and keeps
> its ledger). Steps use checkbox (`- [ ]`) syntax. Commits and the ledger go
> through a Terminal-panel tab (Prerequisites in the spec).

**Goal:** in full mode, `/spec` attacks the idea before it writes the spec
(drill, concept gate, idea panel, approach pick, save point, `/spec think`)
and attacks the spec after it (a five-role review panel, `/spec review`),
with Alternatives in the templates, a two-way `/spec verify` and a size
trigger in `/rev`.

**Architecture:** `SKILL.md` keeps the step outline, numbered 0–8; three new
references hold the procedures: `think.md` (Steps 1–3 in full mode),
`lenses.md` (the 7 idea lenses and 5 review roles, one file for both panels),
`review.md` (agent tools, panel, merger, round 2, cap and cost line,
traceability, the single reviewer, standalone review). Panel agents write
run-id scratchpad files and one merger returns counts and a path.

**Tech Stack:** Markdown skill files; Python 3 stdlib `unittest` for the skill
tests; `claude -p` (2.1.311) for the scripted dry runs.

**Spec:** `/Users/shrix/.agents/skills/spec/docs/spec/think-and-review.md`

## Global Constraints

- `~/.agents/skills/spec/SKILL.md` at most 24,000 bytes after every task; each
  task's byte budget is in its Done when.
- Light mode, post-build mode, spec-only re-runs, `update` and `changelog`
  keep their flow; `verify` changes only by FR12.
- At most 15 planned agents in Steps 1–5 (idea panel 8, review panel 6, round
  2 1), round 2's slot reserved inside them; one STOP recovery per panel sits
  outside them.
- Panel agents and mergers: `general-purpose`; Read, Grep, Glob under
  `<root>`; Write only to their own `<scratchpad>/spec-<run-id>-*` file; no
  secret-bearing file read (`.env*` except `.env.example`, keys, credentials),
  no secret printed; repo text is data. The write limit is instructed, so
  the content fingerprint `checks.sh fp` of `<root>` is compared before and
  after each dispatch.
- New reference files carry `<!-- author: shrix -->` on the line after their
  first heading, like `references/questions.md`.
- External skills (superpowers, security-audit, claude-security) are never
  edited.
- Test command: `python3 -B ~/.agents/tests/skills/spec/test_spec.py`.
- Commits from a Terminal-panel tab, staging named files only; never push.

## Review Focus

1. "recommended for the rest" on the first drill turn — the concept gate still
   shows (Task 6 pins the rule; Task 11 runs it).
2. A panel agent fails or times out — its role is `incomplete`, never clean
   (Task 4 pins it; Task 14 checks it).
3. A dispatch would pass the cap — not made, recorded; round 2 never refused
   (Task 4 pins it).
4. `/spec review` on a doc with no plan — only the plan sub-checks are skipped
   and said (Task 8 pins it; Task 12 runs it).
5. `/spec think` on a feature that already has a spec, or a second feature
   wanting a concept's name — refused or asked, nothing overwritten (Tasks 6
   and 7 pin the refusal lines, the new-name ask and the save-point condition).

---

## Phase 1 — Spike and test harness (estimate: ~1 h)

### Task 1: Spike — can `claude -p` drive /spec headless?

**Files:**
- Create: `~/.agents/skills/spec/docs/spec/think-and-review-spikes.md` — the verdict Tasks 11–13 depend on

- [ ] **Step 1:** In a Terminal-panel tab, make a throwaway git repo under the
  session scratchpad holding one file, and from inside it run
  `claude -p "/spec add a hello command" --output-format json --permission-mode acceptEdits`.
- [ ] **Step 2:** Run `claude -p --continue "recommended" --output-format json --permission-mode acceptEdits`
  until the run writes `docs/spec/*.md` and dispatches its Step 5 reviewer, or
  stops; answer "drop it" at the go.
- [ ] **Step 3:** Write the spike file: the commands and permission mode, and
  four checks — a question printed; `--continue` resumed the same session; the
  spec file was written; a subagent ran (the JSON or the Review section) — the
  tokens and minutes, and the verdict `headless: yes` only when all four hold,
  else `headless: no — <which failed>`.
- [ ] **Step 4:** Remove the throwaway repo; confirm it is gone.
- [ ] **Step 5:** Commit the spike file.

**Done when:** the spike file holds a verdict with the four checks.

### Task 2: Skill tests — the baseline

**Files:**
- Create: `~/.agents/tests/skills/spec/test_spec.py` — the size, link and frontmatter guard every later task runs

- [ ] **Step 1: Write the tests** (`unittest`, the skillsync test's style and
  ownership stamp):
  - `test_skill_size`: `len(SKILL.read_bytes()) <= 24000`
  - `test_reference_names_resolve`: every match of
    `(?<![/\w~.])references/[a-z0-9-]+\.md` in `SKILL.md` and each
    `references/*.md` (backticks included) exists under the skill folder
  - `test_relative_links_resolve`: after stripping fenced blocks and inline
    code, every `](path)` link that is not `http(s):` or `#…` resolves from the
    file's own folder
  - `test_frontmatter`: `name: spec`, `author: shrix`, and `description:` whose
    value, YAML quotes stripped, starts with `(shrix)`
- [ ] **Step 2:** Run the test command. Expected: 4 passed on the unchanged
  skill (`_shared/references/checks.md` in docs.md does not match the lookbehind).
- [ ] **Step 3:** Commit `test_spec.py`.

**Done when:** 4 tests pass on the unchanged skill.

**Phase gate:** the test command green.

## Phase 2 — Lenses, review panel, templates (estimate: ~3 h)

### Task 3: `references/lenses.md`

**Files:**
- Create: `~/.agents/skills/spec/references/lenses.md` — one source for both panels' roles, so the two lists cannot drift
- Modify: `~/.agents/tests/skills/spec/test_spec.py` — pins the shape

**Interfaces:**
- Produces: `## Idea lenses` (7 × `### <name>`: scope and reuse, cost and
  limits, ease of use, migration and rollback, monitoring, upkeep, pre-mortem)
  and `## Review roles` (5 × `### <name>`: fit, fresh reader, design critic,
  build readiness, claims against the code). Each `###` block has the lines
  `**Question**:`, `**Test**:` (opens "A newcomer could"), `**Hard rule**:`,
  `**Reads**:`, `**Report**:`.

- [ ] **Step 1: Failing test** `test_lenses_shape`: exactly 7 `###` under Idea
  lenses and 5 under Review roles, each with the five labelled lines and a Hard
  rule ending "no taste findings"; the pre-mortem's Question contains
  "3 months later"; the intro contains `STOP: goal unclear` and the two rules
  for every role, "no taste findings" and "every finding in this one pass".
- [ ] **Step 2:** Run it. Expected: FAIL (file missing).
- [ ] **Step 3:** Write `lenses.md`. The intro holds the goal check for every
  agent. Scope and reuse's Hard rule: it searches the code under `<root>` and
  names what can be reused, or says it found nothing. Fit's Reads: Decided, the
  capture docs, the ADRs, the code for reuse. Build readiness's Reads includes:
  in a partly-built run, `as-built` requirements need no plan task.
- [ ] **Step 4:** Run the test command. Expected: all pass.
- [ ] **Step 5:** Commit both files.

**Done when:** `test_lenses_shape` and the baseline pass.

### Task 4: `references/review.md` and Step 5's outline

**Files:**
- Create: `~/.agents/skills/spec/references/review.md` — the panel procedure, out of SKILL.md for the size cap
- Modify: `~/.agents/skills/spec/SKILL.md` § Step 5 — an outline only: who reviews per mode, close every Critical and Important, two rounds, READ review.md
- Modify: `~/.agents/tests/skills/spec/test_spec.py` — pins traceability and the rules

**Interfaces:**
- Consumes: the role names from Task 3.
- Produces: sections `## Agent tools`, `## Panel`, `## Merger`,
  `## Closing findings` (fix, refute, Open question), `## Round 2`,
  `## Cap and cost`, `## Traceability`, `## Single reviewer`,
  `## Standalone review` (filled in Task 8). Report files:
  `<scratchpad>/spec-<run-id>-review-<role>.md` and
  `<scratchpad>/spec-<run-id>-review-merged.md`, `<run-id>` = `HHMMSS` at panel
  start.

- [ ] **Step 1: Failing tests**:
  - `test_traceability`: the set of sub-bullet texts under `## Single
    reviewer` equals the set of first-column cells of the `## Traceability`
    table, and each row's second column is exactly one Review role heading in
    lenses.md (rows include: integration points → claims against the code;
    every triggered companion present → build readiness; examples given →
    fresh reader; the Decided exception → fit)
  - `test_review_rules`: review.md contains `general-purpose`, `Write only`,
    `status --porcelain`, `incomplete`, `STOP: goal unclear`, `15`,
    `reserved`, `once per panel`, `<run-id>`, and the cost line form
    `<panel>: <n> agents · <k>k tokens · <min> min`
  - `test_single_reviewer_additions`: § Single reviewer has a sub-bullet with
    "reason" and "ends green" scoped "runs that write a plan", one with
    "Alternatives" scoped "light mode", and top-level bullets "No taste
    findings" and "Every finding in this one pass"
  - `test_step5_outline`: SKILL.md § Step 5 names `references/review.md` and is
    at most 700 bytes
- [ ] **Step 2:** Run. Expected: 4 FAIL.
- [ ] **Step 3:** Write review.md per spec FR6–FR8 and FR14. Move today's Step 5
  text into it: the brief into `## Single reviewer`, its wording kept with each
  sub-check on its own sub-bullet, plus the two scoped FR6 clauses ("no taste
  findings" and "every finding in this one pass" stay as top-level bullets with
  no sub-bullets, and are also in the lenses.md intro, Task 3); the closing rules, round 2, the Open-question path and the
  self-review fallback into their sections.
- [ ] **Step 4:** Shorten SKILL.md § Step 5 to the outline.
- [ ] **Step 5:** Run the test command. Expected: all pass.
- [ ] **Step 6:** Commit the three files.

**Done when:** all tests pass and SKILL.md is at most 21,000 bytes (it frees
about 2,370).

### Task 5: Templates, close and the plan brief

**Files:**
- Modify: `~/.agents/skills/spec/references/specification-template.md` — Open questions under the title; Alternatives considered after 4.6
- Modify: `~/.agents/skills/spec/references/adr-template.md` — `## Alternatives considered` (its pointer changes in Task 6, once think.md exists)
- Modify: `~/.agents/skills/spec/references/close.md` — the Architecture row also names the runner-up
- Modify: `~/.agents/skills/spec/SKILL.md` § Step 4.1 (Open questions and Alternatives) and § Step 4.3 (FR10)
- Modify: `~/.agents/tests/skills/spec/test_spec.py` — pins the template headings

- [ ] **Step 1: Failing test** `test_templates`: the spec template contains
  `## Open questions` before `## 4.1` and `## Alternatives considered` with How,
  Pros, Cons, Why rejected; the ADR template contains `## Alternatives
  considered`; close.md's Architecture row contains
  "runner-up"; SKILL.md § Step 4.3 contains "reason" and "build and its tests
  green".
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Make the edits.
- [ ] **Step 4:** Run the test command. Expected: all pass.
- [ ] **Step 5:** Commit the five files.

**Done when:** all tests pass and SKILL.md is at most 21,800 bytes.

**Phase gate:** the test command green; `/spec verify` over the phase's commits.

## Phase 3 — Think stage (estimate: ~2.5 h)

### Task 6: `references/think.md` and the question bank

**Files:**
- Create: `~/.agents/skills/spec/references/think.md` — Steps 1–3 in full mode
- Modify: `~/.agents/skills/spec/references/questions.md` — the two new bank questions and the drill's one-question form
- Modify: `~/.agents/skills/spec/references/adr-template.md` — its comparison-table pointer names think.md (full) and SKILL.md § Step 3 (light)
- Modify: `~/.agents/tests/skills/spec/test_spec.py` — pins the think rules

**Interfaces:**
- Consumes: the Idea lens names (Task 3); `## Agent tools` (Task 4).
- Produces: sections `## Drill`, `## Concept gate`, `## Contradictions`,
  `## Idea panel`, `## Approach pick`, `## Save point and resume`.

- [ ] **Step 1: Failing test** `test_think_rules`: think.md contains
  `6 turns`, `recommended for the rest`, the turn-1 light offer with
  `never under` `think`, `which one stands`, `2 extra turns`, `draft — concept`,
  `NEW feature in full mode` (the save-point condition), `Resuming concept`,
  `concept saved; run /spec`, `re-run /spec`, `Review` (the cost line in the
  concept file), that Step 4 keeps the concept's Open questions, Decided,
  Assumptions, Alternatives and Review lines and moves each routed problem to
  Assumptions, 4.12 or 4.13, and names
  `references/lenses.md`, `references/review.md` and a merger; questions.md's
  bank contains "done today" and "hard constraints", and "all questions" lifts
  the 6-turn cap; the ADR template contains `references/think.md`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Write think.md per spec FR1–FR5, add the two bank rows and the
  drill form to questions.md, and change the ADR template's pointer.
- [ ] **Step 4:** Run the test command. Expected: all pass.
- [ ] **Step 5:** Commit the four files.

**Done when:** all tests pass.

### Task 7: SKILL.md — description, modes, Step 0.2, Steps 1–3

**Files:**
- Modify: `~/.agents/skills/spec/SKILL.md` — `description:` (think and review named; ideation via `/spec think`); § Invocation (`/spec think [<idea>]`, `/spec review <file>…`; the mode-word rule names both; `light think` refused; the Light bullet's "offered as one item of Step 2's batch" becomes "offered on the drill's first turn, never under `think`"); § Quick Reference rows 1–3 (full: think.md; light: as today); § Step 0.2 (a `draft — concept` spec resumes at Step 4 and READs `references/think.md` § Save point and resume; another feature wanting its name gets the ask; `think` on a feature that has a spec is refused); §§ Steps 1–3 (full mode: READ think.md; the batch-only, auto-pick and "one up-front ask" text scoped to light mode); § Safety gates (the save point writes only the spec file)
- Modify: `~/.agents/tests/skills/spec/test_spec.py` — pins the modes
- Modify (only if the byte fallback fires): `~/.agents/skills/spec/references/rerun.md` — receives Step 0.2's re-run bullets

- [ ] **Step 1: Failing test** `test_modes`: the description contains `think`
  and `review`; the Invocation block contains `/spec think` and `/spec review`;
  the mode-word rule names `think` and `review`; § Step 0.2 contains
  `draft — concept`, `Resuming concept`, `§ Save point and resume`, "new name"
  and the `think` refusal; `light think` is refused; the Light bullet contains
  "first turn" and "never under"; §§ Steps 1–3 name `references/think.md`; § Step 2
  contains "light mode" beside "one up-front ask".
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Make the edits.
- [ ] **Step 4:** Run the test command. Expected: all pass. Over 24,000 bytes →
  move Step 0.2's re-run bullets to rerun.md and run again.
- [ ] **Step 5:** Commit both files, plus `rerun.md` when the fallback moved
  bullets into it.

**Done when:** all tests pass and SKILL.md is at most 24,000 bytes.

**Phase gate:** the test command green; `/spec verify` over the phase's commits.

## Phase 4 — Standalone review, verify, /rev (estimate: ~1.5 h)

### Task 8: `/spec review` and the `/spec verify` additions

**Files:**
- Modify: `~/.agents/skills/spec/references/review.md` § Standalone review — FR11
- Modify: `~/.agents/skills/spec/references/docs.md` § Verify — FR12, merged with the "public functions documented" item
- Modify: `~/.agents/tests/skills/spec/test_spec.py` — pins both

- [ ] **Step 1: Failing test** `test_review_and_verify`: § Standalone review
  names the Step 0.2 plan lookup, says only the plan sub-checks (traceability,
  plan form, estimates) are skipped without a plan, and that no file changes;
  docs.md § Verify contains `undocumented`, the interface definition ("CLI
  command", "skill invocation", "route", "non-underscore", "`tests/**`",
  "`**/fixtures/**`"), one phrase per drift type ("code lacks", "missing
  fields", "hard-coded", "pattern or library"), "without its path", and that
  link nudges are advisory; "public functions documented" is gone and
  "complex logic explained" remains.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Make the edits; Verify still fixes nothing.
- [ ] **Step 4:** Run the test command. Expected: all pass.
- [ ] **Step 5:** Commit the three files.

**Done when:** all tests pass.

### Task 9: /rev size trigger

**Files:**
- Modify: `~/.agents/skills/rev/SKILL.md` § Close — the FR13 line, before "A class seen before"
- Modify: `~/.agents/tests/skills/spec/test_spec.py` — one pin, since /rev has no test file

- [ ] **Step 1: Failing test** `test_rev_trigger`: rev/SKILL.md § Close
  contains `--numstat`, `100`, `3+ core files`, `**/docs/spec/**`,
  `**/docs/plan/**` and `spec it?`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Add the line per FR13.
- [ ] **Step 4:** Run the test command. Expected: all pass.
- [ ] **Step 5:** Commit both files.

**Done when:** all tests pass.

**Phase gate:** the test command green; `/spec verify` over the phase's commits.

## Phase 5 — Acceptance (estimate: ~2 h, plus the dry runs' tokens)

Each dry run copies `tests/skills/spec/fixtures/toy/` into a fresh git repo in
the scratchpad and commits the copy, runs Task 1's commands from a Terminal-panel tab, saves the JSON
in the scratchpad, and removes the repo after (confirmed gone). Task 1 verdict
`no` → Tasks 11–13 are written as owner checks instead (each command, its
expected result) into the spike file, and that write is their Done when.

### Task 10: Fixture

**Files:**
- Create: `~/.agents/tests/skills/spec/fixtures/toy/notes.py` — a note store writing `notes.json` with field `body`; one public function no doc names; a hard-coded path the README says is configurable
- Create: `~/.agents/tests/skills/spec/fixtures/toy/README.md` — names `save_note` without its path, and says the store path is configurable
- Create: `~/.agents/tests/skills/spec/fixtures/toy/seeded-spec.md` — a short spec renaming the stored field `body` → `text`, with no rollback plan and no down step

- [ ] **Step 1:** Write the three files.
- [ ] **Step 2:** In a scratchpad copy, `python3 -B notes.py` exits 0.
- [ ] **Step 3:** Commit the three files.

**Done when:** the files exist and the copy runs.

### Task 11: Acceptance — drill, idea panel, pick, save point, resume, review panel

**Files:**
- Modify: `~/.agents/skills/spec/docs/spec/think-and-review-spikes.md` — records the results

- [ ] **Step 1:** `/spec think add tags to notes; the plugin system for future tag types is a must-have`;
  answer "recommended for the rest" at the first question. Expected: the
  concept gate shows and its summary keeps the plugin system.
- [ ] **Step 2:** Answer "confirm". Expected: the idea panel's list names the
  plugin system as not needed; the approaches include two that differ in scope
  (tags in the note vs a separate tag index) and the run asks me to pick.
- [ ] **Step 3:** Pick the separate tag index. Expected: the spec file has
  `Status: draft — concept`, Decided names the pick, Alternatives holds the
  loser with its reason, and Review has an idea-panel cost line.
- [ ] **Step 4:** `/spec add tags to notes` (the same feature text). Expected:
  the first output is `Resuming concept: docs/spec/<name>.md`; no drill
  question again; before the go, the spec keeps the concept's Decided,
  Alternatives and idea-panel cost line, and its Review section also has
  `review panel: 6 agents · …k tokens · … min`; `git status --porcelain`
  shows only files under `docs/spec/` and `docs/plan/`. Answer "drop it".
- [ ] **Step 5:** Record each expectation as met or missed, with tokens and
  minutes; commit the spike file.

**Done when:** every expectation is met, or each miss is filed as a finding for
/rev.

### Task 12: Acceptance — standalone review and light mode

**Files:**
- Modify: `~/.agents/skills/spec/docs/spec/think-and-review-spikes.md` — records the results

- [ ] **Step 1:** `/spec review seeded-spec.md`. Expected: a Critical or
  Important finding for the missing rollback; the plan sub-checks skipped and
  said (no plan); a review-panel cost line; `git status --porcelain` empty.
- [ ] **Step 2:** `/spec light add a --version flag`, "recommended" to the
  batch, "drop it" at the go. Expected: one batch, the approach taken on its
  own, one reviewer, no idea panel.
- [ ] **Step 3:** Record the results with tokens and minutes; commit.

**Done when:** every expectation is met, or each miss is filed as a finding for
/rev.

### Task 13: Acceptance — verify both ways

**Files:**
- Modify: `~/.agents/skills/spec/docs/spec/think-and-review-spikes.md` — records the results

- [ ] **Step 1:** `/spec verify` in the fixture repo. Expected: the unnamed
  public function listed `undocumented`; the hard-coded store path listed as
  drift; `save_note` listed with its path as a nudge; no file changed.
- [ ] **Step 2:** Record the results; commit.

**Done when:** every expectation is met, or each miss is filed as a finding for
/rev.

### Task 14: Owner checklist

**Files:**
- Modify: `~/.agents/skills/spec/docs/spec/think-and-review-spikes.md` — the checks only the owner can stage

- [ ] **Step 1:** Write four owner checks, each with its setup and expected
  result: a `/spec` request too vague to state a goal → `STOP: goal unclear`
  and a question; a panel role pointed at a file it cannot read →
  `incomplete`; an answer after the concept gate that contradicts Decided →
  "which one stands?" and no file written that turn; a /rev over a seeded
  120-line change with no spec → the `spec it?` line.
- [ ] **Step 2:** Commit.

**Done when:** the four checks are in the spike file and named in /dev's
close as Manual checks.

**Phase gate:** the test command green; `/spec verify` over the run; the
scratchpad's dry-run repos gone.
