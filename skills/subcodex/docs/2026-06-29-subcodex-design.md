# subcodex — design spec

**Date:** 2026-06-29
**Status:** Approved design, pre-implementation
**Skill path:** `~/.agents/skills/subcodex/`
**Related:** `~/.agents/skills/clodex/` (machinery reuse), `codex` plugin runtime
(`codex-companion.mjs`), `~/.agents/skills/_shared/`

---

## 1. Summary & intent

`subcodex` lets Claude Code (CC) **delegate named tasks to background Codex
worker(s)**, keep doing its own work, then **verify → grade → integrate** each
result into its own pipeline.

It is *asymmetric delegation* — distinct from the two existing patterns:

- `codex:codex-rescue` = a thin one-shot **forwarder** (single `task` call,
  returns stdout verbatim, no evaluation, main thread waits).
- `clodex` = a symmetric **dialectic** (Claude and Codex answer the *same*
  question and debate to convergence).
- `subcodex` = CC offloads **different** work to Codex, stays free, then
  **evaluates and integrates** each result. The evaluation + integration step
  is the new capability neither existing skill provides.

A "Codex subagent" here is an **external background Codex process**, not a CC
Task-subagent. Consequences: it runs in Codex's own context (does **not**
consume CC's context window); launching is non-blocking; the result enters CC's
context only as one bounded blob at evaluation time.

## 2. Locked decisions

| Dimension | Decision |
|---|---|
| Work type | Both write **and** read-only, chosen per task |
| Isolation | Worktree for writes; read-only runs in-place |
| Fan-out | Single by default, batch when given a list |
| Evaluation | Verify + grade + integrate, **typed by task** |
| Control | Explicit (you name it); CC may **propose** but must ask first |
| Topology | Approach A — skill-as-orchestrator (main CC thread drives) |
| Code reuse | Full DRY via `_shared/`; migrate clodex in the same effort |
| Build order | `_shared/` helpers → subcodex → clodex migration last (regression-gated) |

## 3. Control model & invocation

### 3.1 Three trigger forms

1. **Slash** — `/subcodex [flags] <task>`. Literal; no inference.
2. **Natural language** — Codex used as a *do-this-task* verb, e.g.
   "let's do task xyz over subcodex", "can we do this in the bkgd over codex",
   "hand this to codex", "offload the migration to codex / run it async".
3. **CC-may-propose** — when CC spots an offloadable chunk mid-work, it states
   so explicitly ("this is a good subcodex candidate because…") and asks. You
   approve/decline. **Never silent.**

### 3.2 Disambiguation rule (because "codex" is a loaded word in this env)

- **subcodex verbs** → *do / implement / handle / offload / run in background /
  async / "over codex"*: delegate the task.
- **clodex verbs** → *settle / debate / weigh in / second opinion / "who's
  right"*: that is the dialectic, not this skill.
- **Incidental** ("I read about codex", code containing the word): do nothing.
- **Ambiguous** → ask one line: "subcodex (delegate it) or clodex (debate it)?"

### 3.3 Confirm-before-launch gate

Inferred forms (NL and CC-may-propose) **always echo the resolved task and wait
for go**. Slash form with an unambiguous task may skip the gate. A misread
background **write** task is expensive to undo; the confirm is cheap.

Confirm echo format:

```
subcodex → "implement the rate-limiter in api/limit.ts"
mode: --write (worktree)   verify: npm test limit   effort: high
Proceed? (yes / edit / cancel)
```

### 3.4 Flags

| Flag | Purpose | Default |
|---|---|---|
| `--write` | Write-capable Codex in a worktree | off (read-only, in-place) |
| `--verify "<cmd>"` | Verification command for the eval step | inferred from project |
| `--effort low\|medium\|high\|xhigh` | Codex reasoning effort | matched to CC model |
| `--model <m>` | Override Codex model | runtime default |
| `--wait` | Block till done instead of background+notify | off (background) |

Effort matching (reuse clodex's table via `_shared/references/codex-effort-match.md`):
Opus→high, Sonnet→medium, Haiku→low, else high+warn. Explicit `--effort`
overrides. Never `--effort minimal` (HTTP 400 with Codex's tool config).

## 4. Architecture & components

### 4.1 Skill layout

```
~/.agents/skills/subcodex/
  SKILL.md                 # the orchestration procedure
  scripts/
    worktree.sh            # add / remove / diff / merge worktree helpers
  references/
    delegate-prompt.md     # frames the task text handed to Codex
    evaluate-write.md      # how CC verifies+grades a write diff
    evaluate-readonly.md   # how CC sanity-checks+grades an analysis
    help.md                # /subcodex help text
  docs/
    2026-06-29-subcodex-design.md   # this spec
```

### 4.2 Shared components (`~/.agents/skills/_shared/`)

Extracted so both clodex and subcodex reuse one source of truth:

| File | What it is |
|---|---|
| `codex.sh` | Companion wrapper. **Dynamic-path** version — globs newest plugin: `ls -d ~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs \| sort -V \| tail -1`. Robust to version bumps (clodex currently hardcodes `1.0.1`). |
| `launch-job.sh` | Launch helper: runs `task --background`, parses the `task-…` job-id, retries until `logFile` is non-null, writes `jobid.txt`/`logfile.txt`, echoes the job-id. |
| `poll-job.sh` | Poll helper: the `until` status-loop to terminal state. Runs backgroundable; exits on terminal job state so the harness notifies CC. |
| `codex-preflight.sh` | `setup --json \| jq -e .ready` auth check. |
| `codex-effort-match.md` | Claude-model → effort table referenced by both skills. |

Skill-specific (NOT shared): subcodex's prompt templates, `worktree.sh` (clodex
never writes), SKILL.md, help.

### 4.3 State & registry

Per-**job** layout (batch = N jobs; a single task is batch-of-1):

```
/tmp/subcodex-state/
  registry.jsonl           # append-only: one line per job (id, task, mode, state)
  <jobslug>/               # slug = timestamp + short task hash
    task.txt mode.txt verify.txt effort.txt
    worktree.txt           # worktree path (write tasks only)
    jobid.txt logfile.txt status.txt session.txt
    result.md              # fetched Codex output
    verify.log             # test/build output (write tasks)
    verdict.md             # CC's grade + decision
```

`registry.jsonl` is the piece that makes "fire several, keep working, see them
all" work: any later invocation (or `/subcodex status`) reads it to enumerate
in-flight jobs **across** invocations, and to reconcile/cancel orphans after a
CC interrupt. clodex doesn't need this (single self-contained dialectic);
subcodex's premise (fire several, walk away) makes it a requirement.

Retention: keep newest N job dirs, purge older at the start of each invocation
(lazy sweep, same approach as clodex).

### 4.4 Constants

| Name | Value | Why |
|---|---|---|
| `MAX_CONCURRENT` | 4 | Cap simultaneous Codex jobs in a batch |
| `MAX_RETRIES` | 1 | Bounded retry on eval failure, then fallback |
| `STATE_ROOT` | `/tmp/subcodex-state` | Temp state, retention-swept |
| `POLL_TIMEOUT` | 20 min | Poller gives up, cancels, offers retry |

## 5. Task lifecycle & data flow

Core loop (single task; batch = this fanned out with a concurrency cap):

```
/subcodex [--write] [--verify "cmd"] <task>
  0. Preflight (codex authed?) + match effort + confirm if inferred
  1. Register: mkdir state/<slug>; write task/mode/verify/effort;
     append registry.jsonl
  2. --write → worktree.sh add <slug>   ⇒ WS = worktree path
     read-only →                          WS = current dir
  3. launch-job.sh: task --background --fresh [--write] --effort E <prompt>
       ⇒ save jobid + logfile
  4. poll-job.sh (background) ───────────────►  CC keeps working
                                                (harness notifies on exit)
  ▼ (notify)
  5. fetch: result <jobid> > result.md
  6. EVALUATE (typed by mode)            [see §6]
  7. DECIDE: pass → integrate ; fail → retry ≤MAX_RETRIES else fallback
  8. cleanup: worktree.sh remove <slug>; write verdict.md
```

**Batch** is triggered when the task input is a list — multiple newline- or
`;`-separated task lines (slash form), or several distinct tasks named in one NL
request. Each line becomes one job. Per-line flags are allowed (e.g. one line
`--write`, another read-only); a leading flag with no per-line override applies
to all. Batch evaluates each job *as it lands* (pipeline, not a barrier) — early
finishers integrate while slow ones still run; `MAX_CONCURRENT` cap in flight.

**Integration never auto-commits to main.** Codex commits on its
`subcodex/<slug>` branch *inside the worktree*; on pass, CC brings that diff
into the main working tree as **unstaged** changes for the user to review and
commit (honors git-safety "commit only when asked"). Conflicts with CC's
parallel edits are **resolved, not discarded**; non-trivial conflicts are
surfaced to the user.

**Verify command resolution (write):** explicit `--verify` wins; else CC infers
the project's test/build; if it can't infer, it runs a lighter compile/build
check **and says so** — never silently claims "verified" without evidence.

## 6. Evaluation (typed by task)

### 6.1 Write tasks

1. Run the verify command **in the worktree** → `verify.log`.
2. Grade: do tests/build pass? Does the diff actually satisfy the task intent
   (not just compile)?
3. Decide:
   - **pass** → integrate the worktree diff into main tree (unstaged).
   - **tests ran and failed** → retry (≤`MAX_RETRIES`) re-delegating with the
     failure log as context; then fallback (CC finishes it / surfaces to user).
   - **verify command could not run** → surface; do **not** claim verified.

### 6.2 Read-only tasks

1. Spot-check the analysis's claims against the real code (don't trust blindly).
2. Grade relevance/quality.
3. Decide: **pass** → use as pipeline input; **fail** → retry or discard with a
   note.

## 7. Isolation & merge-back

- Write tasks run in a dedicated git worktree on branch `subcodex/<slug>`,
  created/removed via `worktree.sh`. CC's main tree is untouched while Codex
  works.
- **Non-git workspace + `--write`:** refuse worktree-write (no isolation
  possible). Offer read-only instead, or explicit in-place-with-warning if the
  user confirms.
- **Isolation boundary (no overclaiming):** the worktree sandboxes the *repo
  working dir*. If Codex writes to an absolute path outside the repo, that is
  bounded by Codex's own sandbox, not by subcodex. subcodex guarantees
  isolation *within the repo* — and the SKILL.md says exactly that.

## 8. Error handling

| Failure | Handling |
|---|---|
| Preflight: codex not authed | Stop; tell user to run `/codex:setup`. No job launched. |
| Job status `failed`/`cancelled` | `result` returns nothing — read logfile, abort job, show diagnostics, offer retry of just that job. |
| Poller times out (>`POLL_TIMEOUT`) | Cancel job, report, offer retry. |
| Empty result | Treat as failure → same diagnostics path. |
| `--write` in non-git dir | Refuse worktree-write; offer read-only or explicit in-place-with-warning on confirm. |
| Worktree add fails (branch collision, dirty) | Report, don't launch; suggest fix. |
| Merge-back conflict | CC resolves (never discards); non-trivial → surface to user. |
| Verify *command* errors (vs tests failing) | Distinguish: tests-failed → retry w/ context; couldn't-run → surface, never claim "verified". |
| User Ctrl+C mid-flight | Background Codex jobs keep running; next invocation reads `registry.jsonl`, cancels non-terminal jobs. |

## 9. clodex migration plan (full DRY — modifies a working skill)

This effort **modifies clodex** (explicitly approved). Changes:

1. Point clodex's `CODEX_SH` constant at `~/.agents/skills/_shared/scripts/codex.sh`.
2. Replace clodex's inline launch blocks (its steps 1a / 2c / 2.6c) with
   `_shared/scripts/launch-job.sh`, and its inline poller blocks (1c / 2e / 2.6e) with
   `_shared/scripts/poll-job.sh`. **Highest-regression-risk change** — the shared
   helpers must reproduce the launch → retry-for-null-logfile → `until` loop
   exactly (clodex gotchas #1, #4).
3. Delete clodex's now-unused `scripts/codex.sh` (clean-changes: no dead files).
4. Update the permission allowlist: add
   `Bash(bash ~/.agents/skills/_shared/scripts/codex.sh:*)`,
   `Bash(bash ~/.agents/skills/_shared/scripts/poll-job.sh:*)`,
   `Bash(bash ~/.agents/skills/subcodex/scripts/worktree.sh:*)`; remove the now
   redundant `Bash(bash ~/.agents/skills/clodex/scripts/codex.sh:*)`.

**Regression gate:** run a real `/clodex` dialectic end-to-end after migration
and confirm it still completes — not just visual equivalence.

## 10. Testing strategy

| Layer | Tests |
|---|---|
| Bash helpers | `worktree.sh add/remove/diff` on a throwaway repo; `codex.sh` resolves newest companion; `poll-job.sh` exits on completed/failed |
| Read-only e2e | `/subcodex "summarize how X works"` → fetched, graded, consumed |
| Write e2e | `/subcodex --write --verify "…" "tiny change"` → worktree → edit → verify → diff applied unstaged → worktree removed |
| Batch e2e | two tasks → both in registry, evaluated independently |
| Failure inject | kill a job → failed path; non-git + `--write` → refusal path |
| clodex regression | real `/clodex` dialectic post-migration (the DRY gate) |

Real-Codex e2e tests stay minimal/bounded (they cost time + tokens) via a small
fixture task.

## 11. Out of scope (YAGNI)

- No autonomous silent delegation (CC must always ask before proposing).
- No dialectic/debate (that is clodex's job).
- No persistent daemon — jobs are per-invocation, tracked in temp state.
- No cross-machine / cloud Codex — local companion runtime only.

## 12. Open risks & future graduation

- **Main-context noise:** raw Codex output + test logs land in CC's context.
  Bounded by "explicit only" + "a few tasks". *Graduation path:* Approach C
  (run verify+grade in a throwaway subagent that returns a compact verdict)
  reuses this entire spine and only swaps the eval step — not a redesign.
- **clodex poller migration** is the riskiest change; gated by the regression
  test in §9.
- **Companion path / runtime contract** may change across `codex` plugin
  versions; dynamic-path resolution mitigates the path, but `task`/`status`/
  `result` flag changes would need a follow-up.
