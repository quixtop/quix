# /spec think stage and review panel
Status: approved 2026-10-27 · built and reviewed 2026-10-28 · EGM adoption closed 2026-10-28

This is the approved design. The built behaviour is in the skill files and
`docs/reqs.md`, which win where they differ; the differences are listed under
§ Review, "As built".

## Open questions

None. The four CRITICAL questions are answered under Decided.

## 4.1 Feature Overview

```
Feature: think stage and review panel for /spec

**One-Line Summary**: in full mode, /spec attacks the idea before it writes
the spec, and a panel of five role reviewers attacks the spec after.
**Problem Statement**: today Step 2 asks one batch and assumes the rest,
Step 3 takes the recommended approach on its own, and one reviewer covers
seven concerns. A weak idea reaches a finished spec, the rejected approaches
are lost, and one reviewer spread over seven concerns misses gaps.
**Success Criteria**:
- A toy feature with a seeded needless part: the idea panel flags it.
- A seeded spec that renames a stored field with no rollback:
  `/spec review` flags it.
- `/spec think` stops at `draft — concept`; a later `/spec` resumes and asks
  no question a second time.
- Light mode keeps its flow: one batch, the approach taken on its own, one
  reviewer, no panels.
- Each panel's agent count, tokens and minutes are in the spec's Review
  section.
- The spec skill tests pass: `SKILL.md` at most 24,000 bytes, every link
  resolves, frontmatter valid, every check of today's reviewer brief owned by
  exactly one role.
```

## 4.2 User Stories

```
As the owner
I want /spec to question my idea over several turns and attack it before it writes anything
So that a weak idea dies before it costs a spec and a build

**Acceptance Criteria**:
- [ ] Given a full-mode run, when Step 2 runs, then it asks one question per turn,
      each with a recommended answer, until scope, security, hard constraints and
      "how is this done today, and why is that not enough?" are answered, or 6
      turns pass, or I say "recommended for the rest"
- [ ] Given the drill ended, when the concept gate shows, then it is a 2–3 sentence
      summary I confirm or correct, and no agent runs before I confirm
- [ ] Given I confirmed, when the idea panel runs, then 7 agents run in one wave
      and one merger gives me a short list of the top problems
- [ ] Given the approaches really differ, when Step 3 ends, then I pick one, and
      each rejected approach keeps its pros, cons and reason

As the owner
I want to think an idea through without writing a spec
So that I can stop at a confirmed concept and come back later

**Acceptance Criteria**:
- [ ] Given `/spec think <idea>` for a new feature, when Step 3 ends, then the spec
      file holds the concept with `Status: draft — concept` and the run stops
- [ ] Given a `draft — concept` spec, when I run `/spec <that feature>`, then it
      announces the resume and starts at Step 4 without asking again

As the owner
I want a spec reviewed from several angles, and any doc reviewable on its own
So that gaps one reviewer misses are caught

**Acceptance Criteria**:
- [ ] Given a full-mode Step 5, when the panel runs, then 5 role reviewers run in
      one wave and one merger writes the merged findings to a file
- [ ] Given an agent that cannot tell what the feature is for and why, when it
      starts, then it returns `STOP: goal unclear`, and the run asks me
- [ ] Given an agent that could not read a file it needed, when it reports, then
      its result is `incomplete`, never clean
- [ ] Given `/spec review <file>`, when it runs, then the panel reviews that file
      and reports findings, and changes no file

As the owner
I want docs checked against the code in both directions, and features disguised as fixes caught
So that drift and unspecced work are found

**Acceptance Criteria**:
- [ ] Given `/spec verify`, when it runs, then it also lists undocumented
      interfaces, the 4 drift types, and doc names with no path
- [ ] Given a /rev range over 100 changed lines (tests, docs and config left out)
      or 3+ core files that no spec or plan names, when /rev closes, then its
      report suggests /spec
```

## 4.3 Functional Requirements

```
FR1: Question drill (full mode, Step 2)
- **Priority**: Critical
- **Input**: the request, the vision formed at Step 1 (not printed in full mode),
  the sources
- **Processing**: turn 1 offers light mode when the small-feature test holds
  (SKILL.md § Invocation, Light), never under `think`; yes → the light batch,
  and the drill ends.
  Otherwise one question per turn from the bank, each with a recommended
  answer and other options; ends when the four required topics are answered
  (scope, security, hard constraints, the current way), at 6 turns, or on
  "recommended for the rest" (on any turn, the first included). The unanswered
  bank items take their recommended answer as Assumptions. The bank gains two
  questions: "how is this done today, and why is that not enough?" and "what
  are the hard constraints?"
- **Output**: Decided and Assumptions
- **Constraints**: light mode keeps the one batch; "all questions" lifts the
  6-turn cap and asks the whole bank, one question per turn

FR2: Concept gate (full mode, end of Step 2)
- **Priority**: Critical
- **Input**: Decided, Assumptions, the vision
- **Processing**: a 2–3 sentence summary (request, goal, benefit, approach,
  scope edge) shown for confirm or correct. A correction updates Decided and the
  gate shows again. From here to the go, an answer that contradicts a Decided
  entry stops all file writes for that turn and asks "which one stands?"
- **Output**: a confirmed concept
- **Constraints**: no agent runs before the confirm; in full mode the Step 1
  vision block is not printed on its own (it is this summary)

FR3: Idea panel (full mode, Step 3, before the approaches)
- **Priority**: Critical
- **Input**: the confirmed concept, `<root>`, `references/lenses.md` § Idea lenses
- **Processing**: 7 agents in ONE wave — scope and reuse (with a real code
  search), cost and limits, ease of use, migration and rollback, monitoring,
  upkeep, and the pre-mortem ("it is 3 months later and this failed: why?").
  Each first does the goal check (states the goal and why in one line, or
  returns `STOP: goal unclear`), then writes its report to
  `<scratchpad>/spec-<run-id>-idea-<lens>.md`. One merger reads the 7 files,
  removes duplicates, ranks, writes `<scratchpad>/spec-<run-id>-idea-merged.md`
  and returns counts and its path. The main conversation shows at most 5
  problems and routes each: a follow-up question (at most 2 extra turns, outside
  the 6-turn cap), an Assumption, an Out of Scope entry or a Risk. The concept
  gate shows again only when a follow-up changed Decided
- **Output**: the routed problems
- **Constraints**: § Agent tools applies (FR14)

FR4: Approach pick (Step 3)
- **Priority**: High
- **Input**: 2–4 approaches with pros, cons, complexity, effort
- **Processing**: full mode: the user picks when the approaches differ in scope,
  security, cost or user flow; otherwise the recommended one is taken as an
  Assumption. Every rejected approach goes into the spec's Alternatives with how
  it works, pros, cons and the reason it lost
- **Output**: the chosen approach in Decided (or Assumptions) and Alternatives
- **Constraints**: light mode keeps today's automatic pick, and still fills
  Alternatives

FR5: Save point and `/spec think`
- **Priority**: High
- **Input**: the end of Step 3
- **Processing**: for a NEW feature in full mode, the run writes
  `docs/spec/<feature>.md` with `Status: draft — concept`, holding Open
  questions, 4.1, Decided, Assumptions, Alternatives, the idea panel's routed
  problems, and a Review section holding the idea panel's cost line. A re-run of
  an existing spec writes nothing at the save point (Step 4 overwrites it as
  today, and rerun.md's recovery covers it). `/spec think` stops here and prints
  how to resume. The re-run check (Step 0.2) treats a `draft — concept` spec as a
  resume: `Resuming concept: docs/spec/<name>.md`, starting at Step 4; when a
  different feature wants the same name, it asks: resume this concept, or a new
  name. Step 0.2's resume READs `references/think.md` § Save point and resume,
  which says Step 4 keeps the concept file's Open questions, Decided,
  Assumptions, Alternatives and Review lines, moves each routed problem to the
  place it was routed to (Assumptions, 4.12 Risks, 4.13 Out of Scope), and adds
  the rest
- **Output**: the concept file
- **Constraints**: `think` is a mode word (alone → the feature from the
  conversation, as bare `/spec`; followed by the idea). `think` always runs full
  mode; `light think` is refused with one line. `/spec think` on a feature that
  already has a spec is refused with one line, nothing written: for a concept
  "concept saved; run /spec <feature>", past it "re-run /spec <feature>
  instead". A resume runs in the mode the user gives (`/spec light
  <feature>` resumes in light mode)

FR6: Review panel (full mode, Step 5)
- **Priority**: Critical
- **Input**: the set (spec, companions, plan), `references/lenses.md` § Review
  roles, `references/review.md`
- **Processing**: 5 role reviewers in ONE wave — fit, fresh reader, design
  critic, build readiness, claims against the code. Each does the goal check
  first. A file it needed and could not read makes its result `incomplete`; a
  failed or timed-out agent is `incomplete` too. Each writes
  `<scratchpad>/spec-<run-id>-review-<role>.md`; one merger writes
  `<scratchpad>/spec-<run-id>-review-merged.md` and returns counts and the path.
  review.md § Single reviewer lists today's brief with each sub-check on its own
  sub-bullet (same wording, lines split); every sub-bullet is owned by exactly
  one role in § Traceability (owners of the four whose owner is not obvious:
  integration points → claims against the code; every triggered companion
  present → build readiness; examples given → fresh reader; the Decided
  exception → fit). The two rules that apply to every role ("no taste findings",
  "every finding in this one pass") go to the lenses.md intro for the panels and
  stay in § Single reviewer as top-level bullets with no sub-bullets. In a
  partly-built run, build readiness is told that `as-built` requirements need no
  plan task
- **Output**: Critical / Important / Minor with file:line, closed as today (fix,
  refute on the record, or an Open question for scope or security)
- **Constraints**: light mode, post-build mode and spec-only re-runs keep the
  single reviewer, whose brief gains two clauses: Plan form, only in runs that
  write a plan — every file in the plan has a reason and every phase ends green;
  Completeness, only in light mode — Alternatives filled

FR7: Round 2 and later rounds
- **Priority**: High
- **Processing**: unchanged trigger (a Critical, scope or security fix). ONE
  fresh reviewer over the fix hunks only; it never re-flags a finding round 1
  closed by a refutation or a Decided entry. Go-with-changes rounds stay one
  reviewer
- **Constraints**: two rounds at most, as today

FR8: Cost record and agent cap
- **Priority**: High
- **Processing**: the planned dispatches in Steps 1–5 are at most 15 (idea panel
  8, review panel 6, round 2 1). Round 2's slot is reserved and never refused.
  A STOP recovery — the stopped agents plus one merger — runs at most once per
  panel, on top of the 15, and is recorded. A go-with-changes round adds one
  reviewer, recorded. Any other dispatch past 15 is not made; the Review section
  says which and why. Each panel's line in the Review section:
  `<panel>: <n> agents · <k>k tokens · <min> min`

FR9: Templates
- **Priority**: High
- **Processing**: the spec template gains `Open questions` directly under the
  title and an `Alternatives considered` section after 4.6 (one block per
  rejected option: How · Pros · Cons · Why rejected); the ADR template gains
  `## Alternatives considered` in the same form, and its pointer to the
  comparison table names `references/think.md` (full) and SKILL.md § Step 3
  (light). close.md's Architecture row also names the runner-up
- **Constraints**: a full-mode spec with no Alternatives entry is an Important
  finding for the design critic

FR10: Plan brief
- **Priority**: Medium
- **Processing**: the writing-plans instructions in Step 4.3 add: every file the
  plan creates or changes carries a one-line reason, and every phase ends with
  the build and its tests green

FR11: `/spec review <file>…`
- **Priority**: Medium
- **Input**: one or more existing docs
- **Processing**: the review panel on those docs, with `<root>` from Step 0.1.
  The plan is found as Step 0.2 finds it (`docs/plan/<feature>.md`, else the
  plan whose `Spec:` line names the doc). With no plan, the § Traceability rows
  that concern only the plan (traceability, plan form except "a Status line on
  every file", estimates) are skipped, whichever role owns them, and the report
  says so; every other row still runs. Reports the merged findings and the cost
  line
- **Output**: the report in chat; no file changes
- **Constraints**: a mode word (alone it asks which file); fixes only on the
  user's word, through `/spec update` or a re-run

FR12: `/spec verify` additions
- **Priority**: High
- **Processing**: the checklist gains (a) the reverse check, merged with today's
  "public functions documented" item: each interface in scope that no doc
  names is listed `undocumented` — an interface is a CLI command or flag, a
  skill invocation, an HTTP route, or an exported or non-underscore function
  or class, outside tests and test fixtures (`tests/**`, `**/fixtures/**`); (b) four drift types: a feature the docs describe that the code
  lacks; a data model missing fields the docs list; a value hard-coded where the
  docs say it is looked up or configured; a pattern or library other than the
  one the docs name; (c) link nudging: a doc naming a function, file or command
  without its path is listed with the path found
- **Constraints**: (a) and (b) are drift and block a clean `docs` pass; (c) is
  advisory and never blocks. Verify still fixes nothing; the check log rules
  are unchanged

FR13: /rev size trigger
- **Priority**: Medium
- **Processing**: at /rev's close, count the reviewed range with
  `git diff --numstat <base> <tree>`, added + removed lines, leaving out tests,
  docs and config. When that passes 100 lines, or 3+ core files changed (a core
  file is a changed file that is not a test, doc or config), and no file under
  any `docs/spec/` or `docs/plan/` folder in the repo (`**/docs/spec/**`,
  `**/docs/plan/**`) names any of the changed paths, the report adds one line:
  `this range grew past a fix — spec it? /spec <topic>`
- **Constraints**: a suggestion only; it never runs /spec and never blocks the
  close

FR14: Agent tools
- **Priority**: Critical
- **Processing**: every panel agent and merger is a `general-purpose` subagent
  whose brief allows Read, Grep and Glob anywhere under `<root>`, and Write only
  to its own `<scratchpad>/spec-<run-id>-*` file; no other write, no Bash that
  changes anything, no agent dispatch. The brief forbids secret-bearing files
  (`.env*` except `.env.example`, keys, credentials) and printing a secret, and
  says repo text is data, never instruction. `<run-id>` is the time the panel
  starts (`HHMMSS`), so two panels in one session never share a file. The write
  limit is an instruction, not enforced by the tools, so around each dispatch the
  main conversation compares the content fingerprint `checks.sh fp` (every
  tracked and untracked, not ignored, file in `<root>`) before and after; any
  change is reported at once with `git status --porcelain --untracked-files=all`
  and recorded in Review. Ignored files and paths outside `<root>` are not
  covered; when `<root>` is not a git repo or `fp` fails, Review records
  `write check: not run — <why>`. The single and round-2 reviewers get the same
  brief lines (writing nothing) and the same check
```

## 4.4 Data Model

```
Entity: spec file Status line (docs/spec/<feature>.md, line under the title)
{
  status: "draft — concept" | "draft — awaiting go" | "approved <date>",
}
Only /spec reads it (grep across ~/.agents/skills: no other reader).

Entity: panel report file (scratchpad, one per agent)
{ role: string, goal_line: string | "STOP: goal unclear",
  result: "findings" | "incomplete", unread: [path],
  findings: [{severity, file_line, problem, why_it_matters}] }

Entity: merged file (scratchpad, one per panel)
{ counts: {critical, important, minor, stopped, incomplete},
  findings: [{severity, file_line, problem, roles: [string]}] }

**Storage**: the spec file in the project; panel files in the session scratchpad
**Lifecycle**: panel files end with the session; their findings and cost lines
live on in the spec's Review section
```

## 4.5 UI/UX Specification

N/A — no UI. The chat interaction (one question per turn, the concept gate, the
short problem list) is specified in FR1–FR4; the forms live in
`references/think.md`.

## 4.6 Technical Architecture

```
~/.agents/skills/spec/
├── SKILL.md                         description, modes (think, review), Step 0.2
│                                    resume, Steps 1–3 and 5 as outlines, light text
│                                    scoped to light
├── references/think.md         NEW  drill, concept gate, contradictions, idea panel,
│                                    approach pick, save point, resume
├── references/lenses.md        NEW  the 7 idea lenses and 5 review roles: each a
│                                    question, a written test, one hard rule, what it
│                                    reads, its report form
├── references/review.md        NEW  agent tools, panel, merger, goal check,
│                                    incomplete rule, round 2, cap and cost line,
│                                    traceability, the single reviewer, standalone
│                                    review
├── references/questions.md          two new bank questions; the drill form
├── references/specification-template.md   Open questions on top, Alternatives
├── references/adr-template.md       Alternatives considered; pointer updated
├── references/docs.md               Verify: reverse check, drift types, link nudging
└── references/close.md              Architecture row names the runner-up
~/.agents/skills/rev/SKILL.md        Close: the size trigger line
~/.agents/tests/skills/spec/test_spec.py   NEW  size, links, frontmatter, shapes,
                                           traceability
```

Data flow: Step 1 → drill → concept gate → idea panel (7 → merger) → approach
pick → save point → Step 4 → review panel (5 → merger) → Step 6. The merged
files keep the raw panel output out of the main conversation.

SKILL.md byte budget (22,792 today, cap 24,000): Step 5 (3,070 bytes) shrinks
to an outline of at most 700 bytes, with the reviewer brief, the closing rules,
round 2, the Open-question path and the self-review fallback moving to
review.md (about −2,370); the plan's limits (21,000 after Task 4, 21,800 after
Task 5, 24,000 after Task 7) allow Tasks 5 and 7 about 3,500 together.
Fallback if a task passes the cap: move Step 0.2's re-run bullets to rerun.md.

## Alternatives considered

```
Everything inline in SKILL.md
- How: the new steps written into SKILL.md itself
- Pros: one file to read
- Cons: SKILL.md is 22,792 bytes now; the 24,000-byte cap would break
- Why rejected: size; the step outline stops being readable

A separate /think skill
- How: a new skill for the drill and the idea panel, handing off to /spec
- Pros: /spec stays as it is
- Cons: the question bank and the roles exist twice and drift apart; two
  skills to keep in step
- Why rejected: duplication (modify before create)

Invoke superpowers:brainstorming for the drill
- How: /spec calls the external skill, then overrides its gate and path
- Pros: less text of our own
- Cons: its own approval gate and `docs/superpowers/…` path clash with our single
  go and `docs/spec/`; it is external, so every update can break the flow
- Why rejected: Decided 3

One reviewer with a longer brief
- How: keep Step 5's single reviewer, add the new checks to its brief
- Pros: cheapest
- Cons: one agent spread over seven concerns is the problem this solves
- Why rejected: it keeps the gap

Agents return reports in their final message (no files)
- How: built-in read-only agents; the main conversation collects the reports
- Pros: truly read-only tools
- Cons: all raw panel output lands in the main conversation, and no merger can
  read it
- Why rejected: context cost; FR14's scoped write keeps the output out
```

## 4.7 API Contracts

```
/spec think [<idea>]        the think stage only (full mode); stops at draft — concept
/spec review <file>…        the review panel on existing docs; reports only
/spec verify [scope]        unchanged invocation; more checks (FR12)
```

The mode-word rule extends to `think` and `review`: a mode only when it stands
alone or is followed by what it takes (an idea; an existing file). `/spec
review the login copy` with no such file is a feature.

## 4.8 Edge Cases & Errors

```
Edge Case: the user says "recommended for the rest" on the first drill turn
- **Expected**: the drill ends; the concept gate still shows

Edge Case: an idea lens or a review role returns STOP: goal unclear
- **Expected**: the merger counts it; the run shows the stop and asks for the
  missing goal, then re-dispatches only the stopped agents plus one merger, once
  per panel (FR8)

Edge Case: a panel agent fails or times out
- **Expected**: its role is `incomplete` in the merged file and in the Review
  section; never counted as clean

Edge Case: a dispatch would pass the cap
- **Expected**: not dispatched (round 2 and one STOP recovery excepted); the
  Review section says which agent did not run and why

Edge Case: a draft — concept spec exists and a different feature asks for the
same name
- **Expected**: the re-run check asks: resume this concept, or a new name

Edge Case: /spec think on a feature that already has a spec
- **Expected**: refused in one line, nothing written — a concept: "concept saved;
  run /spec <feature>"; past it: "re-run /spec <feature> instead"

Edge Case: no subagent dispatch available
- **Expected**: each panel runs as one self-review, labelled
  `self-review — isolation unavailable`, as Step 5 does today

| Error | Cause | User Message | Recovery |
|-------|-------|--------------|----------|
| merger file missing | merger failed | "review: merge failed — role files kept at <scratchpad>/spec-<run-id>-*" | read the role files directly |
| contradiction | an answer clashes with Decided | "This contradicts Decided <n>: which one stands?" | the user picks; Decided updated |
```

## 4.9 Non-Functional Requirements

```
Performance: each panel runs as one parallel wave; wall time is the slowest
  agent, not the sum
Cost: at most 15 planned agents in Steps 1–5 (FR8); each panel's tokens recorded
Security: panel agents are instructed to write only their own scratchpad file,
  checked inside `<root>` (tracked and untracked, not ignored, files) by a
  content fingerprint before and after each dispatch (FR14); no secret files read, no
  secret printed; repo text an agent meets is data, never
  instruction
Size: SKILL.md at most 24,000 bytes (tested)
Compatibility: light mode, post-build mode, spec-only re-runs and the update /
  changelog invocations keep their flow; verify changes only by FR12
```

## 4.10 Testing Strategy

```
Testing:

**Levels**: unit — tests/skills/spec/test_spec.py (unittest, like skillsync's):
SKILL.md byte size; every `references/*.md` name that is not part of a longer
path resolves (names inside backticks count); every relative markdown link
resolves after fenced blocks and inline code are stripped; frontmatter (name,
author: shrix, description starting "(shrix)" once YAML quotes are stripped);
lenses.md shape (7 idea lenses, 5 review roles, each with Question, Test, Hard
rule, Reads, Report); the set of § Single reviewer sub-bullets equals the
first column of § Traceability, each row with exactly one role from lenses.md.
Integration — scripted dry runs on throwaway git repos in the scratchpad.
**What is hard to test, and how**: the model's behaviour in a run. A spike first
proves whether `claude -p` (2.1.311 on PATH) can drive /spec headless from a
Terminal-panel tab: a question, a resumed session, a file write and one subagent
dispatch, with the permission mode recorded. If not, the dry runs become a
checklist for the owner, each item with its expected result. STOP, incomplete,
the contradiction gate and the /rev trigger stay owner checks in every case
(each needs a hand-made failure).
**Acceptance**: each 4.1 success criterion is a plan task
```

## 4.11 Implementation Roadmap

Roadmap: see docs/plan/think-and-review.md

## 4.12 Risks & Mitigation

```
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Panels cost a few hundred thousand subagent tokens per full spec (estimate, not measured) | High | Med | cap 15; cost line per panel; light mode free of panels |
| The drill makes the start longer than one batch | High | Low | 6-turn cap; "recommended for the rest"; the light offer on turn 1; the save point |
| A check of today's brief is lost in the split into roles | Med | High | one traceability row per sub-check + a test that parses the brief |
| Lenses produce taste findings | Med | Med | each role's hard rule ends "no taste findings" |
| Author bias when refuting panel findings | Med | Med | every refutation shown at the go, as today |
| Headless dry run not possible here | Med | Med | spike first; owner checklist as the fallback |
| SKILL.md passes 24,000 bytes | Med | Med | per-task byte budget; the named fallback move (4.6) |
| /dev cannot write ~/.agents/.git from Bash | High | High | Prerequisite: commits and the ledger through a Terminal-panel tab |
| A panel agent writes outside its scratchpad file (the limit is instructed, not enforced) | Low | High | `checks.sh fp` compared before and after each panel; a change reported at once (FR14) |

Spike notes: `docs/spec/think-and-review-spikes.md`, written by the plan's
Task 1 (can `claude -p` drive /spec headless?); Tasks 11–13 depend on it.

**Rollback Plan**:
1. `git -C ~/.agents revert <the feature's commits>` — skill files only; no data
2. After a revert, Step 0.2 no longer knows `draft — concept`: list the concept
   files (`grep -l 'Status: draft — concept' **/docs/spec/*.md`) for the owner to
   finish or remove

**Feature flag / kill switch**: N/A — `/spec light` already gives the old flow per run
```

## 4.13 Out of Scope

```
Explicitly Excluded:
- Section-by-section approval gates: against the single go. Future: No
- Walking through findings one by one at the go: built as its own feature,
  `docs/spec/go-walkthrough.md`
- Per-folder contract docs for /spec docs (EGM bootstrap): Future: Yes
- docs/designs and a sitemap index: Future: No
- Running every reviewer twice (A/B): doubles cost. Future: No
- Live isolation probe, scenario files that run, link and size checks for every
  skill: a separate pass on the skill tests. Future: Yes
- The panels in post-build mode and spec-only re-runs: one reviewer is enough
  there (post-build docs are checked against the code), and a panel costs 6
  agents instead of 1. Future: No
- /dev, /dep, /push changes: none needed
```

## Decided

1. Agent cap: idea panel 6 lenses + pre-mortem + 1 merger (8), review panel 5
   roles + 1 merger (6), round 2 one reviewer; at most 15 planned in Steps 1–5;
   tokens recorded per panel.
2. The drill: one question per turn with a recommended answer; ends when scope,
   security, hard constraints and the current way are answered, at 6 turns, or
   on "recommended for the rest".
3. Our own drill in `references/questions.md` and `references/think.md`, taking
   brainstorming's techniques; superpowers:brainstorming is not invoked.
4. Proof: the scripted dry runs (a seeded needless part, a seeded spec with no
   rollback), the `/spec think` resume, light mode's flow unchanged, agent and
   token counts recorded, the skill tests pass.
5. Full mode only; light mode keeps one batch, the automatic pick and one
   reviewer. `/dev`, `/dep`, `/push` unchanged.
6. `/spec think` is part of the `/spec` flow: a plain `/spec` runs the same
   steps without stopping; `think` stops at the save point.
7. Go with changes (Step 6): all 17 round-2 findings applied.

## Assumptions

- Approach B: SKILL.md keeps the outline with step numbers 0–8; the procedures
  go to `references/think.md`, `lenses.md`, `review.md`.
- Docs for this feature live under `~/.agents/skills/spec/docs/` (secscan's
  per-skill layout); git root `~/.agents`.
- `/spec review` reports only; fixes go through `/spec update` or a re-run.
- The panels run only for new full-mode features and full re-runs before a
  build; post-build and spec-only keep one reviewer.
- Each agent checks the goal itself (no separate context-check agent).
- The 24,000-byte SKILL.md cap (EGM's) is adopted for /spec.
- Round 2's slot is reserved inside the 15; one STOP recovery per panel sits
  outside it (FR8): the cap limits planned spend, never a required review.
- A core file, for the /rev trigger: a changed file that is not a test, doc or
  config.

## Prerequisites

- /dev's commits and its ledger (`.git/devloop-ledger.md`) go through a
  Terminal-panel tab, since Bash in this session cannot write `~/.agents/.git`
  (as in the secscan build). Alternative: the owner allows `.git` writes for the
  run.

## To file

Filed 2026-10-28 into `docs/reqs.md`, `docs/arch.md` and `docs/tasks.md`; no
design entries, no ADR files (no `docs/adr/`). Those files hold the current
entries — this list is not kept beside them.

## Review

Today's single-reviewer Step 5 (the panel is what this feature builds).

- Round 1: 1 agent · 158k tokens · 5.8 min — 0 Critical, 14 Important, 18
  Minor; all 32 fixed in the spec and plan. The reviewer ran one write probe
  (`touch ~/.agents/.git/zz_probe`) against its read-only brief; auto mode
  denied it and nothing was written.
- Round 2 (the fixes touched security and data loss): 1 agent · 146k tokens ·
  4.9 min — 0 Critical, 7
  Important, 10 Minor, logged here, not fixed (the two-round rule):
  - I1 plan Task 5: the ADR pointer names `references/think.md` before Task 6
    creates it → Task 5 fails its own link test. Move the edit to Task 6.
  - I2 plan Task 4: `test_traceability` as written is circular and splits into
    35 fragments; two bullets apply to every role. Give each sub-check its own
    sub-bullet, move the all-role rules to the lenses.md intro, assert set
    equality.
  - I3 cap wording: FR8 puts round 2 inside the 15; Assumptions, To file and
    the plan's constraints say outside. Use FR8's model everywhere.
  - I4 FR12(a) counts test functions and the seeded fixture as interfaces → the
    Phase 5 verify gate can never pass. Leave `tests/**` and `**/fixtures/**`
    out.
  - I5 FR1's turn-1 light offer can switch a `think` run to light. Add "never
    under `think`".
  - I6 FR5: a resume never reaches the save point; `think` on an existing
    concept is undefined; "full mode" missing. Define it (refuse: "concept
    saved; run /spec <feature>").
  - I7 Step 4 does not say it keeps the concept file's Decided, Assumptions,
    Alternatives, routed problems and idea-panel cost line; Task 11 Step 4 checks
    only one cost line.
  - M8–M17: rerun.md edit is dead text; 4.6 names too few moved parts; the new
    single-reviewer clauses misfire in post-build and spec-only; FR11's skipped
    checks named by role, not by row; "all questions" vs the 6-turn cap; the
    docs.md test would drop "complex logic explained"; Review Focus 5 not
    pinned; 4.9 overstates write limits (instructed, not enforced — add a `git
    status` check after each panel and a risk row); "100 non-test lines" wording;
    "implicit" should read "not obvious".
- Go with changes (Decided 7): all 17 round-2 findings above applied.
- Go-with-changes round: 1 agent · 137k tokens · 4.2 min — 0 Critical, 2 Important, 10 Minor; all 12
  fixed: I1 the single reviewer keeps the two all-role rules; I2 the resume
  READs think.md § Save point and resume. The 10 Minor (Open questions in the
  Task 6 test; rerun.md in Task 7's fallback; one byte budget; Phase 5 commits
  the fixture copy; the write check's limits and the non-git case; SKILL.md's
  Light sentence in Task 7; the Task 5 "green" pin; this section; FR11 keeps
  the Status-line row; where routed problems go) are `fixed — not re-reviewed`.
- Open: none.

### As built (/dev 2026-10-28, then /rev from ca79040)

Where the build and its /rev differ from the FRs above:

- **FR1, FR2** — light is taken only on an explicit yes; answers found in the
  request or code are Assumptions until the gate; the drill also skips what an
  existing spec's Decided answers; required topics are bank rows 1, 2, 4, 5, 6.
  § Contradictions covers an idea-panel problem too, and a gate correction,
  follow-up answer or go with changes never triggers it.
- **FR3** — the run routes every problem itself (no confirm); a 5th route
  sends a Decided-contradicting problem to § Contradictions (past the 2
  follow-ups, an Open question); every problem not shown is kept in Review.
  think.md lists the only turns that ask.
- **FR4** — a user's pick is Decided.
- **FR5** — Step 0.2 refuses `/spec think` on an exact match or on built code
  ("already built — /spec docs"); a resume needs an exact match and also
  applies § Contradictions; "Step 4 after a save point" (resume or not) keeps
  the concept, ADR drafts and every Review record; spec-only re-runs skip the
  think stage.
- **FR6, FR7** — one § Checks table (sub-check · group · role) replaces the
  Traceability table and the single-reviewer list; each role gets its rows,
  the run (Step 5 or standalone), and build readiness the template paths; the
  single reviewer gets the whole table, the reviewer brief and the "Every
  agent" list (round 2 and go-with-changes too); the light Alternatives row
  accepts `N/A — one viable approach`.
- **FR8** — the 15 counts the panels and review rounds only; a no-go return
  starts a fresh review count (7); `<n>` counts the merger; post-build readers
  are outside the count.
- **FR11** — the feature request is the doc's 4.1 or title, `<feature>` its
  file name; a doc that is not a /spec spec also skips the spec-structure rows.
- **FR12** — interface = exported, else top-level non-underscore, its
  docstring counting; tests excluded by Update's filter plus fixtures; a scoped
  run blocks only on interfaces it added or changed (older gaps pre-existing);
  `/spec update` gives each new interface a doc; link nudges, the complex-logic
  note and `(planned)` entries listed as owed never block.
- **FR13** — counted on the final tree with an inline core-file classifier;
  binary rows count as files; a spec names a path by its repo-relative path or
  its path from that `docs/`'s folder.
- **FR14** — two brief variants (panel/merger, reviewer); the write check runs
  once per wave; an agent that cannot write returns its report inline and the
  merger takes it.
- **4.4** — the report's `result` also takes `stopped`. **4.6** — SKILL.md is
  under its 24,000-byte cap; `tests/skills/spec/fixtures/toy/` holds the fixture.

/rev (base ca79040): full tier · 2 rounds · round 1 4 reviewers 627k tokens
(0 C · 23 I · 63 M), round 2 1 reviewer 173k tokens (0 C · 6 I · 8 M). Every
Critical and Important fixed and test-pinned (17 tests; 52 of them fail on the
pre-fix tree); round 2's fixes are `fixed after round 2 — not re-reviewed`.
