---
name: devloop
author: shrix
description: "(shrix) Implement an already-planned, user-reviewed plan to completion, unattended — a flat set of TASKS, or PHASES each holding tasks: per task anchor → test → implement → verify → isolated review → refactor+docs → commit; an exit gate at every phase boundary (once at the end for a flat plan); a compaction-proof ledger; a close proving every plan item shipped green. NOT planning — input is a reviewed plan. Not for a single task or exploratory work. OFFER it and get a yes first; never auto-run. Triggers on handing over a reviewed plan to run unattended."
metadata:
  version: "1.0"
  category: workflow
---

# devloop — implement a reviewed plan (tasks, or phases of tasks), unattended

## What this is
Pure IMPLEMENTATION of work that is already planned. devloop drives it to
completion in one continuous run and proves the result.

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
stop — do not quietly fix it mid-run (`strict-scope`). Planning belongs to
`superpowers:writing-plans` / `/spec`, before this skill is invoked.

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
4. **Gate, once:** "ok to auto-commit each task as it completes?" One yes
   covers the whole run (`git-safety`'s explicit-commit-ask, run-scoped).

## The loop
For EACH phase, in order — and for each task within it. (Flat plan: one
implicit phase, so this is simply "for each task".)

    1. anchor    restate the task's acceptance criterion (one checkable line)
    2. test      failing test FIRST where testable — proves the gap is real
    3. implement in the main conversation, never via a subagent
    4. verify    build/compile/lint + the task's RELEVANT tests green
    5. review    context-isolated subagent (`verification.md` § Code Review).
                 The dispatch BRIEF is free here: the task's anchor (step 1)
                 plus the plan decisions that bound it — the reviewer gets
                 the intent, never the author's ambient context.
                 Its SKIP rules apply per task: a task that is a typo fix,
                 single config value, single-line fix, or doc-only edit
                 skips review — but the skip rule is NAMED in its ledger
                 line, never silent
    6. refactor  apply critical/important findings — NOT open-ended cleanup.
                 Behaviour is preserved: the task's tests still pass
                 unchanged, or it is a feature change wearing a refactor
                 label. A task that genuinely IS a refactor uses `/refactor`
                 (its golden rules + modes); step 6 never grows into one.
                 DOCS move in the SAME change (`docs-conventions`);
                 anything touched re-runs step 4
    7. commit    one task = one commit; append the ledger line

Then the **EXIT GATE**, which devloop owns (the plan need not contain it) —
at every phase boundary in a phased plan, once at the end of a flat one:
- the FULL suite — catches cross-phase regressions while they are cheap
- docs coherence — `arch.md` / `reqs.md` / `DESIGN.md` actually describe
  what this phase built
- capture per `requirements-capture` (reqs / arch / design / tasks)
- record the phase complete in the ledger

…then begin the next phase IMMEDIATELY.

## Continuous — never pause at a phase boundary
One invocation completes the whole job. Never ask "shall I continue?".
The run STOPS for exactly four things:
- a gate that cannot be made green
- a user-action item that blocks (from the pre-flight scan, or newly found)
- a decision genuinely the user's — destructive, irreversible, or
  outward-facing (`git-safety` / `strict-scope`)
- the user interrupting

Review findings, red tests, and CONTEXT COMPACTION are NOT stops — fix and
carry on. On any real stop, report: where it stopped, what is needed to
resume, and exactly what is already committed.

## Durability — the run outlives its context
Track progress in `.git/devloop-ledger.md` (inside `.git/`, so it needs no
gitignore — same trick as `dep`'s `.git/dep-stamp`), never only in todos.
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
- **Green**: the full suite passes (skip only if the last phase gate just
  ran it green with nothing committed since — don't pay twice).
- **Reviewed**: every task's isolated review passed, its findings were
  fixed, or its named skip rule is in the ledger. Say so.
- **Documented**: docs describe what now exists; captures filed.
- **Clean**: nothing left running (`resource-hygiene`).
Close with the completion status table, then the branch closeout via
`superpowers:finishing-a-development-branch` when it applies.

## Proportionate
Scale to the stakes (`effort-calibration`). A batch of typo fixes does not
earn acceptance criteria and per-task isolated reviews; the full shape is
for work that ships. When trimming, say which steps were dropped and why —
a silently shortened loop reads as a completed one.
