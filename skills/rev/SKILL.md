---
name: rev
author: shrix
description: "(shrix) Review → fix → test until clean, at most two rounds, over a caller's base/range (optionally a path list) or audit findings by ID, else everything since the last push (uncommitted included); with nothing to review it offers /code-audit. An isolated reviewer sized to the change (a tiny diff skips it), a failing test before each fix; round 2 re-reviews only the fix hunks, and only after a Critical or security fix or a fix that adds logic. Triggers on /rev, 'review and clean up what I pushed', 'tighten the recent changes'. NOT one-pass review (/code-review, /simplify) or plan execution (/dev)."
metadata:
  version: "3.2"
  category: workflow
---

# rev — review, refactor, test, until clean

A LOOP, not a pass — thorough in round 1, and at most two rounds. rev owns
**review, refactor and the test-first gate** — nothing else
(`~/.agents/skills/CONVENTIONS.md` § Skill boundaries).
Everything below delegates: rev owns only the ORDER, the gate and the stop
condition.

| it calls | for | why not reimplement |
|---|---|---|
| `/code-review` | the per-round review | one pass, never rechecks its own `--fix` |
| `/simplify` | quality-only cleanup | one pass |
| `/test` | a missing harness or new suite | rev never hand-rolls one |
| `/spec verify` | docs its fixes may have staled | doc sync is spec's alone |
| `dev` | — | implements a PLAN; rev improves existing code |

A check that an earlier skill already passed on this exact tree is skipped, not
repeated — the check log, `~/.agents/skills/_shared/references/checks.md`
(read it before the first check; `checks.sh` below is
`bash ~/.agents/skills/_shared/scripts/checks.sh`). Which tests a round runs,
and flaky ones: `~/.agents/skills/_shared/references/test-runs.md`.

## Scope — what gets reviewed

Everything since the base SHA, uncommitted work included — "what I changed"
is what you want reviewed, not what you remembered to commit — plus what it
touches: the callers and importers of changed code, and the tests naming
them. The base SHA:

1. The caller's scope: a base SHA, or a `BASE..HEAD` range's BASE (as
   `/spec verify` takes), optionally with `--paths <file>` (one repo-relative
   path per line): only those
   paths' changes are then in scope, and the review questions below carry
   the same `--paths <file>`.
2. Else the last push: `git rev-parse @{push}`.
3. Failing that, `origin/<current-branch>`.
4. No caller scope, and no remote, or no change since the last push,
   committed or not → nothing to review:
   say so and OFFER `/code-audit` for a whole-repo pass, whose findings come
   back as `/rev A1 A4`. Never start an audit unasked — it is heavy, and its
   design lens spends Codex tokens.

**Audit findings by ID** (`/rev A1 A4`, as `/code-audit`'s Next steps hand
them over): read those findings from the newest audit entry in
`docs/logs/revlogs.md`. They are round 1's findings — round 1 starts at step
2, Check — the base is that entry's SHA, and no new audit runs. An ID that
entry does not hold is named and dropped. A Minor named by ID (an older
entry's `Nit` reads as Minor) is fixed like an Important: the user asked for
it. Round 1 has no review of its own, so its fixes always get round 2's
isolated review before the run can close. The check log's `has review` and
`since review` shortcuts do not apply here — the named findings are the
work, whatever an earlier pass covered.

## Pre-flight (once)

- Record the base SHA before round 1: it bounds the run; the close cites it.
- **Peers.** `/test` and `/spec` should be in your skills list. One
  missing → name it, and do its part without it: no `/test` → write the
  failing test in the existing harness; with no harness either, a fix is
  held, never landed untested, and the close lists it as needing one; no
  `/spec` → the close says docs were not verified.
- **Ask once.** Anything rev needs from the user is asked here, in one batch,
  before round 1; after that it runs to the close without stopping. The only
  mid-run ask is a safety gate's: a delete — a file, or dead code, which is
  listed first and removed only on a yes (`references/refactoring-playbook.md`).
- **Already reviewed?** (never for audit findings by ID — § Scope)
  `checks.sh has review --base <base>` exit 0 → this
  range passed review on this exact tree: say so and close. Else
  `checks.sh since review --base <base>` exit 0 → round 1 reviews only the
  change since that passed tree (`checks.md` § Before a check). A caller's
  `--paths <file>` rides both questions.
- **Baseline.** Run the tests the base..tree change affects ONCE —
  tier the diff with `test-runs.md`'s table — unless `checks.sh has
  affected-<tier>[,each higher tier],tests --base <base>` exits 0
  (`checks.md`): then the baseline is all green, and the line saying so
  replaces the run. On that `has` miss, `checks.sh since tests` exit 0 (a full
  pass under 12 hours old) → run only the tier table's selection for the paths
  it lists that the base..tree change also touches; the rest passed in that
  full run. A whole-selection baseline that comes back green, with no test
  excused as flaky, records `checks.sh pass affected-<tier> --by rev --base
  <base> --tree <the fp taken before it>`; a pre-existing failure or the
  shrunken run records nothing. The baseline, the cheap gates and
  round 1's review dispatch (step 1) start together in ONE message: all three
  only read the tree, and no fix lands until the baseline returns. A caller
  that runs its suite alongside the review supplies the baseline:
  rev runs none of its own, and applies no fix until that run returns. A test already
  failing before round 1 is recorded as pre-existing — failing before this
  run's fixes, not necessarily at the base SHA — and never attributed to this
  run: without that line, round 2 blames itself for round 0's breakage.

## The loop (round N)

1. **Review — isolated, sized to the change** (audit findings by ID: round 1
   starts at step 2, § Scope). The cheap gates — lint, typecheck and build
   where the project has them — run beside it in the baseline's wave, and the
   brief says so, so no review is spent on what a linter catches. Their
   failures inside the scoped diff join step 3's batch; one that predates the
   base is recorded as pre-existing, like a failing test; a fix that changes
   behaviour still gets its failing test first (step 4).
   **Tiers** — set by what the change touches; lines are only an upper cap:
   - *Tiny* — no new logic: wording, renames, config values, comments or
     docs, or a fix in one spot whose correctness the diff itself shows → no
     subagent. The report names the skip: `review: skipped — tiny (<why>)`.
   - *Small* — new or changed logic in one area, with no changed interface or
     signature, no stored data or schema, no concurrency, no security, and
     under ~150 changed lines → ONE reviewer subagent with `model: sonnet`,
     handed the hunks (the scoped diff with `-U10`), told to read no changed
     file whole unless a hunk is cut off, checking correctness and the list
     below, and reporting findings only — no strengths or recommendations
     sections.
   - *Full* — everything else, and ALWAYS security-adjacent, auth, payments
     or data-migration code whatever its size → the session model and the
     full brief below.
   Round 2 is sized the same way over its fix hunks, but never as tiny: it
   runs only because a fix needs a second look.
   Dispatch a context-isolated subagent
   over the scoped diff: in a loop the author grading his own work compounds,
   and by round 2 it is confirming its own fixes. The dispatch states what
   changed and where, the acceptance criterion and the deliberate decisions.
   It bounds the diff tree to tree — `git diff -U10 BASE "$(checks.sh fp)"`,
   which holds this loop's own fixes and every untracked file, new folders
   included; after a `since` shrink, `git diff -U10 <since line 1> <since
   line 2> -- <the listed paths>` — and with nothing committed it says the
   tree is uncommitted.
   Keep the brief narrow — a round costs minutes per file the reviewer opens
   (owner 12Oct26): save the scoped diff to a file in the scratchpad and hand
   over its path; name each changed function and, on the full tier, its
   direct callers, which it reads instead of whole files (the small tier reads
   the hunks only); it runs single test files only, never a whole
   project (minutes each, and the load fails timing tests running beside it).
   Slices with no file or caller in common go to parallel reviewers in ONE
   message: the round then takes its slowest slice, not their sum.
   Round 1 is the complete pass: it reviews that whole diff, and the brief
   tells the reviewer to report EVERY finding in one go — no later round
   catches what it skips. Round 2 reviews only
   `git diff -U10 <the fp taken before round 1's dispatch — for an audit-ID
   run, which has none, before its first fix> "$(checks.sh fp)" -- <every
   file the fixes edited, created, deleted or renamed (both paths), their
   tests included>` — round 1's fixes, tree to tree so new files and
   failing-first tests show, and files the fixes did not touch stay out. When
   either `checks.sh fp` call fails: `git diff -U10 BASE -- <those files>`,
   plus each of them that is untracked as `git diff -U10 --no-index /dev/null
   <file>` —
   with its findings and the callers of each function a fix changed in the
   brief; anything it finds outside those hunks is listed for the user, never
   fixed inside the loop.
   The reviewer is read-only (another revision goes in a git worktree) and
   spawns nothing; it checks correctness, security (OWASP,
   secrets), scope creep, dead code, error handling at boundaries and the
   project's conventions, and returns Critical / Important / Minor, each
   with `file:line`. Every item on that list is a finding; style preferences
   are not: a reviewer told to find gaps always finds some, and chasing
   taste is how a loop over-engineers.
   No subagent → ONE self-reviewed round, labelled
   "self-review — isolation unavailable", then close.
2. **Check** each finding and its severity against the code; a false
   positive is refuted on the record, not fixed.
3. **Fix ALL Critical + Important in ONE batch** — and any Minor named by ID
   (§ Scope): the minimal fix each, no refactoring inside a fix round. Other
   Minor findings accumulate in a list for the close, untouched, and never
   trigger a round; every Critical and Important is fixed, or refuted on the
   record with a reason or a passing test.
4. **Failing test FIRST, for every bug.** Write the test that reproduces the
   finding, watch it fail, then fix. A fix lands when the previously-failing
   case passes — not when the edit is written. No harness or suite to extend
   → `/test` builds one; rev writes only the failing test.
5. **Run only the tests that touch the fixed code** — the fixes' own and
   failing-first tests, plus what the tier table (`test-runs.md`) picks for
   the fix hunks: no worse than the baseline. A fix-only run: it neither asks
   nor records.
   A failing test is re-run once alone first; whether a pass alone excuses it
   as flaky is `test-runs.md`'s rule — a flaky one is named in the close,
   never fixed in code.
6. **Count** open Critical + Important, plus any open Minor named by ID.
7. **Gate:**
   - the round's review found zero Critical + Important → close (say so and
     stop — zero findings is a result, not a reason for another pass)
   - round 1 had its own isolated review, and every finding still to be
     closed was Important, each now fixed — on its failing-first test where
     the finding is testable (step 4; dead code, logging or a lint fix has
     none) — none closing a security finding and none adding logic beyond its
     finding → close (owner 12Oct26). The test that failed first and passes
     now is the fix's proof; a review of the fix re-reads the same lines at a
     full round's cost. The close lists them as "fixed, test-pinned" — an
     untestable one as "fixed — no test, not re-reviewed", and then the close
     records no review.
   - round 1, and a fixed finding was Critical or security, or a fix added
     logic beyond its finding, or round 1 had no review of its own (audit
     findings by ID, § Scope) → round 2, over the fix hunks only (step 1)
   - ⚠️ **round 2 ending → close, never a third round.** Its Important fixes
     on failing-first tests close as "fixed, test-pinned", like round 1's. A
     round-2 fix that would have earned another round — it closed a Critical
     or security finding, or added logic beyond its finding — is named "fixed
     after round 2 — not re-reviewed". Anything neither fixed nor refuted, or a Critical or
     security fix that no isolated review saw → STOP: report what is
     unresolved and why, truthfully. Same principle as "after two failed
     corrections, step back" — a loop without a cap spins forever on a
     finding it cannot fix.

## Close

Before the report, run the tests that touch this run's fixes, all rounds'
(`test-runs.md`), that the last round's step 5 did not already run on the
final tree — none when it ran them all, or when the whole run changed
nothing: it must be no worse than the baseline, and a failing test the
baseline did not run counts as a regression. Worse → the regression is a
Critical finding: back into the loop while rounds remain, else STOP. rev
runs no full suite, so it records no `tests` pass, and this fix-only run
records no `affected-*` pass. Then
record what passed (`checks.md` § Recording — the fingerprint is taken with
`checks.sh fp` BEFORE each round's review dispatch): zero open Critical +
Important after an isolated review → `checks.sh pass review --by rev --base
<base> --tree <fp before the last round's review>` — or, when the gate closed
on test-pinned fixes, the fp of the final tree, taken after its last test
run: those fixes stand on their tests, so the next caller must not review
them again.
A run scoped by a caller's `--paths <file>`, a STOP close, a self-review, a
tiny skip or a fix "fixed after round 2 — not re-reviewed" records no review:
none of them reviewed the whole range's lines in isolation (a `--paths`
caller reads this run's result directly). Nor does an
audit-ID run: its round 2 sees only the fix hunks, never the whole range.

One report: base SHA · review tier (a tiny skip named) · rounds run ·
findings by severity · what was fixed ·
the accumulated MINOR list, unfixed and named · the PRE-EXISTING list (what
the reviewer saw outside the change: listed, never fixed here) · flaky tests ·
what is outstanding and why · test delta against the baseline · what was
skipped as already passed · and one line, also written to the revlog entry:
`Review: <tier> · <n> round(s) · found <C>C/<I>I/<M>M · fixed <n> · refuted
<n> · pre-existing <n> · <min> min · <k>k reviewer tokens`. No finding is silently dropped (step 3) —
that is indistinguishable from missing it.

**A fix that grew into a feature gets `/spec` suggested.** Count the whole
base range on the final tree, `git diff --numstat <base> "$(checks.sh fp)"`
(fp fails → `git diff --numstat <base>`): added plus removed lines of core
files — a core file is one that is not a test (a path matching
`(^|/)(tests?|specs?|__tests__)/`, `test_`, `conftest.py` or `[._](test|spec)\.`),
not a doc (`*.md`, `docs/**`) and not config (`*.json`, `*.y*ml`, `*.toml`,
`*.ini`, `*.cfg`, `*.conf`); a binary row counts as a file, 0 lines. Either
the lines pass 100 or 3+ core files changed; in both cases only when no file
under any `**/docs/spec/**` or `**/docs/plan/**` names a changed core file by
its repo-relative path, or by its path relative to the folder holding that
`docs/` (a bare basename does not count). Then the report adds one line:
`this range grew past a fix — spec it? /spec <topic>`. A suggestion only: it
never runs `/spec` and never blocks the close. A `--paths` run counts only
its paths; an audit-ID run and an "already reviewed" close skip it.

**A class seen before gets a guard proposed.** When a Critical or Important
finding's class already appears in an earlier revlog or deplog entry of this
project, or in a machine-traps file the setup keeps (when present), the
close proposes the guard that would stop it at its source — a rule line, a
lint, a test, a script check — with where it would go. Proposed only: it is
written on the user's yes, never inside the run.

**Docs are not rev's.** When a fix changed behaviour, an interface, a
path or a command, hand off to `/spec verify` over the base SHA before
closing, and name its result in the report. rev never edits docs itself:
that would make it a second docs owner.

## References — the HOW

This file owns the WHEN; these own the HOW.

| file | for |
|---|---|
| `references/refactoring-playbook.md` | modes, golden rules, operations, smells, maintenance passes (performance → `/tune`) |
| `references/code-smells.md` | detailed before/after examples |
| `references/design-patterns.md` | pattern consistency |
| `references/async-migration.md` | sync → async conversions |

## Proportionate

The tiers (loop step 1) match the review to the change — effort follows risk
and reversibility, and never escalates to a billed review tier (such as
`/code-review ultra`) unless the user asks. A tiny diff gets no review, and a
clean round 1 ends the run: say so rather than manufacturing findings to
justify another pass.
