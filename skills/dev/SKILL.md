---
name: dev
author: shrix
description: "(shrix) Run an already-reviewed plan to completion, unattended — flat tasks or phases; per task: test → implement → verify → isolated review → commit, with an exit gate at every phase boundary and a compaction-proof ledger. Triggers on /dev, 'dev this plan', or handing over a reviewed plan to run unattended — never on the bare word 'dev' in ordinary talk. OFFER it and get a yes first; never auto-run. Given only a rough idea, it offers /spec first. NOT planning, a single task, or exploratory work."
metadata:
  version: "1.1"
  category: workflow
---

# dev — implement a reviewed plan (tasks, or phases of tasks), unattended

## What this is
The whole dev cycle for work that is already planned — build, review,
refactor, test — driven to completion in one continuous run, with the result
proved. dev is the one skill allowed to span those capabilities inside a
single loop (`~/.agents/skills/CONVENTIONS.md` § Skill boundaries).
Documentation is not among them: doc sync belongs to `/spec` alone, so
dev CALLS it rather than checking docs itself.

A check an earlier skill already passed on this exact tree is skipped, not
repeated — the check log, `~/.agents/skills/_shared/references/checks.md`
(read it before the first gate; `checks.sh` below is
`bash ~/.agents/skills/_shared/scripts/checks.sh`). Which tests a task runs,
and flaky ones: `~/.agents/skills/_shared/references/test-runs.md`.

**Two input shapes, both native — say which one you read in pre-flight:**

| shape | what you get |
|---|---|
| **flat** — a set of TASKS, no phases | the task loop, then ONE exit gate at the end |
| **phased** — PHASES, each holding TASKS | the task loop per phase + an exit gate at EVERY phase boundary |

A flat list is a single implicit phase — not a degraded mode; the loop and
the gate are identical, there is simply one boundary instead of several.
Never invent phases to group a flat list: the boundaries are the user's
plan structure, and inventing them adds gates they did not ask for.
Conversely never flatten a phased plan — its boundaries are where
cross-phase regressions get caught cheaply.

It does NOT plan, re-scope, or redesign. If the plan is wrong, say so and
stop — do not quietly fix it mid-run; the run does what the plan says, and
a necessary edit beyond it is named, with its reason, before it is made.
Planning belongs to
`/spec` (its plan written by `superpowers:writing-plans`), before this
skill is invoked. **Given a rough idea and no reviewed plan**, say so and
offer `/spec` (`/spec lite` for a small feature): it writes and reviews the
plan, then offers `/dev`. Never improvise a plan inside the run.

NOT for: a single task (ordinary flow), exploratory work, or a batch of
trivia — see § Proportionate.

## Pre-flight (once, before any code)
1. **Read the plan.** Name the SHAPE first — flat or phased (§ What this
   is) — then restate the counts it implies: task count for a flat plan,
   phase count plus task count per phase for a phased one, and the
   acceptance criterion of the first task. Stating the shape back is how
   the user catches a plan you misread as flat when it had phases, before
   an unattended run acts on that reading. If the plan has no checkable
   criteria, derive one line per task and show them — an unattended run
   without anchors produces plausible code that solves the wrong problem.
2. **USER-ACTION SCAN — the whole point of doing this first.** Walk EVERY
   task and list everything the run cannot do by itself:
   credentials/secrets/API keys, external service or account setup,
   billing, a physical device, a permission only the user holds, or a
   decision the plan left open. Surface them ALL now in ONE list, each with
   exactly what is needed. Resolve or work around whatever can be helped
   from here. An unattended run must never discover these one at a time.
3. **Ordering check.** A task consuming another task's output must come
   after it; flag any inversion before starting rather than dead-ending at
   it. Note tasks that are genuinely blocked until an earlier phase lands —
   those are legitimate mid-run pause points, and saying so up front means
   the pause is expected rather than a surprise.
4. **Peers.** `/spec` and `/rev` should be in your skills list. One
   missing → name it now and carry on without it: no `/spec` → every doc
   step is logged "not run — /spec not installed" and the close is not
   Documented; no `/rev` → a refactor task runs through this loop's own
   steps, said so in its ledger line.
5. **Gate, once:** "ok to auto-commit each task as it completes?" — not
   asked when the user's own rules already say to commit finished work. One
   yes covers the whole run; commits are always new (never amended), hooks
   are never skipped, files are staged by name, and nothing is pushed.

Steps 2 and 5 go to the user as ONE batch — every question the run needs,
asked once. After the answer the run asks nothing more; it stops only for
§ Continuous's stops.

## The loop
For EACH phase, in order — and for each task within it. (Flat plan: one
implicit phase, so this is simply "for each task".)

    1. anchor    restate the task's acceptance criterion (one checkable line)
    2. test      failing test FIRST where testable — proves the gap is real
    3. implement in the main conversation, never via a subagent. Before
                 writing a helper, check the codebase for an existing
                 utility or pattern that already does it, and reuse it.
                 A change to stored data or a public interface goes
                 expand → migrate → contract, so old readers keep working
                 until the last step: inventory its consumers first; every
                 migration gets a rollback (a down() for each up()) and is
                 tried on production-sized data; a risky switch rides
                 dual writes or a feature flag
    4. verify    build/compile/lint + the tests the task affects green —
                 tier the diff with `test-runs.md`'s table, base = the
                 task's start commit; ask and record `affected-<tier>`
                 per `checks.md`; a failing test is re-run once alone
                 first, and only `test-runs.md`'s rule can excuse it as
                 flaky — named in the ledger, never fixed in code. No
                 leftover debug output (console.log, print, debugger) and
                 no new console errors or warnings
    5. review    sized per task by WHAT it touches; lines only cap it.
                 Security-adjacent, auth, payments or data-migration code
                 is FULL whatever its size. Otherwise:
                 TINY — no new logic: wording, renames, formatting, config
                 values, comments or docs, or a fix in one spot whose
                 correctness the diff itself shows → no subagent; the
                 ledger line names it, never silent:
                 `review: skipped — tiny (<why>)`.
                 SMALL — new or changed logic in one area, with no changed
                 interface or signature, no stored data or schema, no
                 concurrency, no security, under ~150 changed lines → ONE
                 reviewer with `model: sonnet`, told to open no changed
                 file whole unless a hunk is cut off and to report
                 findings only (no strengths or recommendations sections).
                 FULL — everything else → a reviewer on the session's
                 model.
                 The reviewer is a context-isolated subagent — a fresh one
                 that never saw the implementation. It is read-only
                 (another revision goes in a git worktree) and spawns
                 nothing. Its brief is narrow — each file it opens costs
                 minutes: the task's hunks, tree to tree so every new file
                 and folder shows (`git diff -U10 HEAD "$(checks.sh fp)"`;
                 the tree is uncommitted), saved to a file in the
                 scratchpad and handed over by path; each changed function named, plus — on
                 the full tier — its direct callers, which it reads instead
                 of whole files; single test files only, never a
                 whole project. It checks correctness, security (OWASP,
                 secrets), scope creep, dead code, boundary error handling
                 (no swallowed errors), hard-coded values and magic
                 numbers, logging where a failure must be traceable, and
                 project conventions, and returns Critical / Important /
                 Minor with file:line — EVERY finding in this one pass, as
                 no later round catches what it skips; every item on that
                 list is a finding, style preferences are not. Fix or
                 refute every Critical and Important with a reason or a
                 passing test; list the Minor ones. No subagent available →
                 a self-review labelled as such, never a skipped review.
                 The dispatch BRIEF is free here: the task's anchor (step 1)
                 plus the plan decisions that bound it — the reviewer gets
                 the intent, never the author's ambient context.
                 Take `checks.sh fp` before each dispatch: round 2 reviews
                 `git diff -U10 <the fp taken before ROUND 1's dispatch>
                 "$(checks.sh fp)" -- <every file the fixes edited,
                 created, deleted or renamed (both paths), their tests
                 included>` — tree to tree, so new files show, and files
                 the fixes did not touch stay out. When either `checks.sh
                 fp` call fails: `git diff -U10 HEAD -- <those files>`,
                 plus each of them that is untracked (the task's new files
                 are) as `git diff -U10 --no-index /dev/null <file>` —
                 and step 6 may record it
    6. refactor  fix every Critical and Important finding in ONE batch —
                 a failing test first where testable, the minimal fix, NOT
                 open-ended cleanup and no refactoring inside the fix —
                 then re-run build/lint and only the tests that touch the
                 fixed code (tier the diff with `test-runs.md`'s table
                 over the fix hunks; a fix-only run neither asks nor
                 records). Behaviour is otherwise preserved: the task's
                 tests still pass unchanged, or it is a feature change
                 wearing a refactor label. ROUND 2 runs only when a fixed
                 finding was Critical or security, or a fix added logic
                 beyond its finding: a fresh reviewer, sized by the same
                 tiers but never tiny-skipped, over ONLY the fix hunks; what it
                 finds outside them is listed for the user, never fixed
                 here. Its findings are fixed or refuted with no third
                 round, each fix labelled `fixed after round 2 — not
                 re-reviewed` in the ledger; a Critical still open after
                 round 2 is a stop (§ Continuous). Minor findings never
                 start a round.
                 A run of a SINGLE task: its review saw the whole run
                 range, so once it closes with zero open Critical +
                 Important it is recorded, before the DOCS step below
                 (`pass` needs the tree it saw) — `checks.sh pass review
                 --by dev --base <HEAD when the run began> --tree <fp>`:
                 the fp taken
                 before its last round when that round left nothing to
                 fix; else, when the last round was round 1 and its fixes
                 needed no round 2, a fresh `checks.sh fp` once their
                 tests pass — they stand on their tests. A tiny skip, a
                 self-review or a fix after round 2 records nothing.
                 A task that genuinely IS a refactor uses `/rev`,
                 scoped to the commit the task started from; step 6 never
                 grows into one.
                 DOCS move in the SAME change via `/spec update` (it
                 sweeps old names and replaces, never appends), and any
                 generated doc it reports stale is regenerated here;
                 anything else touched re-runs step 4's build/lint and
                 tests over what it touched — a fix-only run: it neither
                 asks nor records
    7. commit    one task = one commit; append the ledger line

Then the **EXIT GATE**, which dev owns (the plan need not contain it) —
at every phase boundary in a phased plan, once at the end of a flat one:
- the tests this phase affects — tier the diff with `test-runs.md`'s table,
  base = the phase's start commit; ask and record `affected-<tier>` per
  `checks.md` — catches cross-phase regressions
  while they are cheap. A flat plan's single gate is also the run close's
  test run (§ Run close)
- the `/spec update` capture below runs first, since it writes files;
  then the phase's test run and `/spec verify` start together in one wave
- capture new requirements, architecture and design decisions, and deferred
  tasks through `/spec update` over this phase's commits — spec owns the
  reqs / arch / design / tasks families (current-state entries in each doc's
  existing structure, superseded in place, arch entries with their one-line
  why). Hand it what this phase decided; dev never writes those docs itself
- THEN docs coherence — `/spec verify` over this phase's commits, so the
  captures just made are checked too; it owns the check that the arch / reqs /
  design families (every related file, e.g. `arch.md` and `docs/arch/**`)
  describe what was built
- record the phase complete in the ledger

…then begin the next phase IMMEDIATELY.

## Continuous — never pause at a phase boundary
One invocation completes the whole job. Never ask "shall I continue?".
The run STOPS for exactly five things:
- a gate that cannot be made green — three fix attempts on the same failure
  is the limit, and the report names all three; a Critical review finding
  still open after round 2 (loop step 6) counts. Stopping, not deferring: setting
  the task aside would mean discarding or stashing its half-done changes
- a user-action item that blocks (from the pre-flight scan, or newly found)
- a decision genuinely the user's — destructive, irreversible, or
  outward-facing (a push, a delete, a design or structural change, a write
  outside the project tree, a change to anything that isn't the user's own)
- a commit that cannot be made cleanly (something else staged, a secret-scan
  hit, a rejected commit hook)
- the user interrupting

Review findings, red tests, and CONTEXT COMPACTION are NOT stops — fix and
carry on. On any real stop, report: where it stopped, what is needed to
resume, and exactly what is already committed.

## Durability — the run outlives its context
Track progress in the ledger at `$(git rev-parse --git-path devloop-ledger.md)` —
inside the git dir, so it needs no gitignore (`.git/devloop-ledger.md` in a normal
checkout). Never hardcode `.git/…`: in a linked worktree `.git` is a FILE and the
write fails. Never track progress only in todos. The file keeps the name
`devloop-ledger.md`: runs already in progress resume from it.
Append one line per completed task and per completed phase, naming the
commits. On resume — new session, post-compaction — trust the ledger and
`git log` over recollection, and restart at the first entry not marked
complete. Re-running completed tasks is the most expensive failure this
loop has.

## Run close — the bug-free bar
The run is done only when ALL of these hold, each stated explicitly:
- **Complete**: every task in the plan is implemented and committed, or
  explicitly listed as deferred with the reason. No task silently skipped —
  reconcile the plan against the ledger, item by item.
- **Green**: the tests the whole run affects pass — tier the diff with
  `test-runs.md`'s table over the whole run's diff, base = the run's start;
  ask and record `affected-<tier>` per `checks.md` — skipped when that `has`
  exits 0, or when a flat plan's exit gate just ran them with nothing
  changed since. The full suite is not dev's: the whole-system pass is
  `/dep`'s gate, so dev records no `tests` pass. Where
  the project measures coverage, state the new code's coverage against its
  target (80% when the project sets none) and name any shortfall; where it
  measures performance, state that no measured path got slower.
- **Reviewed**: every task's isolated review passed, its findings were
  fixed, or its named tiny skip is in the ledger. Say so. Per-task reviews
  never saw the whole range at once, so they record nothing in the check log
  and never stand in for `/rev`'s review — except a single-task run's review,
  which saw the whole run range and is recorded with the run's start as
  `--base` (loop step 6); name whether it was recorded.
- **Documented**: `/spec verify` passed over the run (skip only if the
  last phase gate just ran it with nothing committed since); captures filed.
  It starts in the same wave as the Green test run — the two are independent.
- **Clean**: nothing left running — every server, watcher, background job,
  browser, tunnel and container the run started is stopped and confirmed
  gone, and temp files it wrote outside the scratchpad are removed.
- **Manual checks**: a short list for the user of what the tests cannot
  cover — a UI flow, a real device, a live account — each with the action
  that proves it and the expected result. "None" is a valid answer; say it.
Close with the completion status table, then the branch closeout via
`superpowers:finishing-a-development-branch` when it applies.

## Proportionate
Scale to the stakes: effort follows risk and reversibility. A batch of typo fixes does not
earn acceptance criteria and per-task isolated reviews; the full shape is
for work that ships. When trimming, say which steps were dropped and why —
a silently shortened loop reads as a completed one.
