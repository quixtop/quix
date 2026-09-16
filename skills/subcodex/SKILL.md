---
name: subcodex
author: shrix
description: (shrix) Delegate named tasks to background Codex worker(s), keep working, then verify/grade/integrate each result. ONLY invoke when the user explicitly delegates a task to Codex — e.g. "/subcodex <task>", "do X over subcodex", "run this in the bkgd over codex". subcodex DELEGATES work; it is NOT clodex (which debates a question). Do not trigger on incidental mentions.
---

# subcodex — Orchestration Procedure

`subcodex` offloads named tasks to one or more background Codex workers, keeps
Claude Code (CC) free to continue other work, then evaluates → grades → integrates
each result. This is *asymmetric delegation* — distinct from:

- `codex:codex-rescue` — thin one-shot forwarder; main thread waits; no evaluation.
- `clodex` — symmetric dialectic; Claude and Codex answer the *same* question and
  debate to convergence.
- `subcodex` — CC offloads **different** work to Codex, stays free, evaluates and
  integrates each result. The evaluation + integration step is what neither existing
  skill provides.

For flags and usage summary, see `references/help.md`.

---

## Section 1 — Invocation & Disambiguation

### 1.1 Three trigger forms (spec §3.1)

1. **Slash** — `/subcodex [flags] <task>`. Literal; no inference.
2. **Natural language** — Codex used as a *do-this-task* verb, e.g.
   "let's do task xyz over subcodex", "can we do this in the bkgd over codex",
   "hand this to codex", "offload the migration to codex / run it async",
   "run this in the background over codex".
3. **CC-may-propose** — when CC spots an offloadable chunk mid-work, it states
   so explicitly ("this is a good subcodex candidate because…") and asks.
   You approve or decline. **Never silent.** CC must always ask before proposing.

### 1.2 Disambiguation rule (spec §3.2)

Because "codex" appears in many contexts, classify before acting:

- **subcodex verbs** → *do / implement / handle / offload / run in background /
  async / "over codex"*: delegate the task (this skill).
- **clodex verbs** → *settle / debate / weigh in / second opinion / "who's right"*:
  that is the dialectic, not this skill — invoke the `clodex` skill instead.
- **Incidental** — "I read about codex", code containing the word, config references:
  do nothing.
- **Ambiguous** — if you genuinely cannot tell, ask exactly one line:
  > "subcodex (delegate it) or clodex (debate it)?"

---

## Section 2 — Confirm-before-launch Gate (spec §3.3)

Inferred forms (natural-language and CC-may-propose) **always echo the resolved task
and wait for go** before launching. A background **write** task is expensive to undo;
the confirm is cheap.

Slash form with an unambiguous task may skip the gate. When in doubt, confirm.

**Confirm echo format** (verbatim):

```
subcodex → "<resolved task>"
mode: <--write (worktree) | read-only>   verify: <cmd|inferred>   effort: <level>
Proceed? (yes / edit / cancel)
```

Wait for the user to respond before proceeding to Section 3.

---

## Section 3 — Flags & Effort Match (spec §3.4)

For full flag reference, see `references/help.md`.

| Flag | Purpose | Default |
|---|---|---|
| `--write` | Write-capable Codex in a git worktree | off (read-only, in-place) |
| `--verify "<cmd>"` | Verification command for the eval step | inferred from project |
| `--effort low\|medium\|high\|xhigh` | Codex reasoning effort | matched to CC model |
| `--model <m>` | Override Codex model | runtime default |
| `--wait` | Block until done instead of background+notify | off (background) |

**Effort matching** — read from `~/.agents/skills/_shared/references/codex-effort-match.md`.

---

## Section 4 — Preflight

Before registering any job, check Codex authentication:

```bash
bash ~/.agents/skills/_shared/scripts/codex-preflight.sh || stop with "/codex:setup"
```

If the preflight fails, stop immediately. Tell the user to run `/codex:setup` to
authenticate. Do not launch any job.

---

## Section 5 — State & Registry (spec §4.3)

### 5.1 Constants

```
STATE_ROOT=/tmp/subcodex-state
MAX_CONCURRENT=4
MAX_RETRIES=1
POLL_TIMEOUT=20   # minutes
```

### 5.1b Resolve `$REPO`

After preflight and before any per-job state setup, resolve the repository root once:

```bash
REPO=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

Read-only tasks may run in a non-git directory; in that case `REPO` equals the current
directory. `--write` mode still requires a git repo — the non-git refusal in §6.2
already covers that case.

### 5.2 Per-job directory layout

```
/tmp/subcodex-state/
  registry.jsonl           # append-only: one JSON line per job
  <jobslug>/
    task.txt               # the task text sent to Codex
    mode.txt               # "write" or "readonly"
    verify.txt             # verify command (or "inferred")
    effort.txt             # effort level used
    ws.txt                 # launch workspace (worktree path for --write, $REPO for read-only); used for cancel
    cwd.txt                # workspace root ($REPO) at invocation time
    prompt.txt             # final delegate prompt (from delegate-prompt.md template)
    jobid.txt              # Codex task-… id
    logfile.txt            # Codex log path
    launch.log             # raw codex task output; job-id parsed from here
    status.txt             # terminal status (completed/failed/cancelled)
    result.md              # fetched Codex output
    verify.log             # test/build output (write tasks only)
    verdict.md             # CC's grade + decision
```

### 5.3 Slug and state setup

```bash
SLUG="$(date +%s)-$(echo "$TASK" | cksum | cut -d' ' -f1)-$RANDOM"   # $RANDOM guards same-second duplicate-text collisions in batch fan-out
SD="/tmp/subcodex-state/$SLUG"; mkdir -p "$SD"
echo "$REPO" > "$SD/cwd.txt"
# write task.txt mode.txt verify.txt effort.txt via the Write tool
```

After writing the per-job files, append one JSON line to `registry.jsonl`:

```bash
echo "{\"slug\":\"$SLUG\",\"task\":\"$TASK\",\"mode\":\"$MODE\",\"effort\":\"$EFFORT\",\"state\":\"launched\",\"ts\":$(date +%s)}" \
  >> /tmp/subcodex-state/registry.jsonl
```

`registry.jsonl` is an **append-only launch index** — one line per job, written at
launch, never rewritten. The authoritative state for each job lives in its per-job
`status.txt` (written by the poller). Do **not** update registry entries after the
fact; read `status.txt` to determine current state.

### 5.4 Retention sweep (lazy, on each invocation)

At the start of every invocation, keep the **newest 10** job dirs (by mtime) and
remove older ones. Two steps, so every issued command matches the permission
allowlist with literal paths (an `xargs rm` form would prompt every time):

```bash
# 1) list job dirs beyond the newest 10 (mtime order).
#    find, not ls: -type d excludes SYMLINKS. /tmp is world-writable, and
#    `rm -rf link/` follows the link and deletes its TARGET — a planted symlink
#    under /tmp/subcodex-state gets arbitrary deletion. Errors are NOT silenced:
#    a sweep that fails forever while reporting success is the worse failure.
find /tmp/subcodex-state -mindepth 1 -maxdepth 1 -type d \
  -exec stat -f '%m %N' {} + 2>/dev/null | sort -rn | tail -n +11 | cut -d' ' -f2-
# 2) if step 1 printed anything, remove those dirs with LITERAL paths, e.g.:
#    rm -rf /tmp/subcodex-state/<slug-a> /tmp/subcodex-state/<slug-b>
```

This prevents unbounded growth while keeping recent job dirs inspectable.
(`registry.jsonl` at the state root is a file, not a dir — the sweep never touches it.)

### 5.5 Orphan reconciliation

**Must run BEFORE the retention sweep (§5.4).** The sweep deletes per-job dirs
(including `jobid.txt` and `ws.txt`); reconciliation needs those files to cancel
orphan jobs. Always run §5.5 first, then §5.4.

Also on fresh invocation: any prior-session job whose poller never wrote a terminal
status to `status.txt` is an orphan (the Codex job may still be running). Determine
terminal state from each job's own `status.txt` — **not** from the registry's
`state` field (which is always `"launched"` and is never updated).

```bash
# Enumerate all known slugs from the registry (or by listing $STATE_ROOT/*/)
for slug in $(jq -r '.slug' "$STATE_ROOT/registry.jsonl" 2>/dev/null | sort -u); do
  st=$(cat "$STATE_ROOT/$slug/status.txt" 2>/dev/null)
  case "$st" in
    completed|failed|cancelled|timeout)
      continue  # terminal — not an orphan
      ;;
  esac
  # Non-terminal (status.txt missing/empty/"launched") — potential orphan
  jid=$(cat "$STATE_ROOT/$slug/jobid.txt" 2>/dev/null)
  # Resolve launch workspace: ws.txt (set at launch) preferred; fall back to cwd.txt
  ws=$(cat "$STATE_ROOT/$slug/ws.txt" 2>/dev/null \
       || cat "$STATE_ROOT/$slug/cwd.txt" 2>/dev/null \
       || echo /tmp)
  if [ -n "$jid" ]; then
    if bash ~/.agents/skills/_shared/scripts/codex.sh "$ws" cancel "$jid"; then
      # Cancel succeeded — write terminal status so this slug is skipped next time
      echo "cancelled" > "$STATE_ROOT/$slug/status.txt"
      # Tell the user the job was cancelled
    else
      # Cancel failed — do NOT claim cancellation; note it for the user
      :
    fi
  else
    # jobid.txt missing (job never launched) — note for user; nothing to cancel
    :
  fi
done
```

**Never** report a cancel that did not happen. **Never** use the label
`cancelled-orphan` — the in-vocabulary value written to `status.txt` is `cancelled`.
If `jobid.txt` is missing or the cancel command fails, tell the user explicitly so
they can investigate.

---

## Section 6 — Worktree Setup (spec §7)

### 6.1 Write mode

```bash
WS=$(bash ~/.agents/skills/subcodex/scripts/worktree.sh add "$REPO" "$SLUG")
# read-only: WS="$REPO"
```

`worktree.sh add` creates a dedicated git worktree on branch `subcodex/$SLUG`
and prints its path. Codex works only within that worktree; the main working
tree is untouched while Codex runs.

### 6.2 Non-git refusal (--write in non-git dir)

**Non-git workspace + `--write`:** refuse immediately. Worktree isolation requires
git. Offer alternatives:

1. Read-only mode instead (no worktree needed).
2. Explicit in-place-with-warning if the user confirms (last resort).

Never silently proceed with `--write` when isolation is unavailable.

### 6.3 Isolation boundary

The worktree sandboxes the *repo working dir*. If Codex writes to an absolute path
outside the repo, that is bounded by Codex's own sandbox, not by subcodex. subcodex
guarantees isolation *within the repo*.

### 6.4 Worktree add failure

If `worktree.sh add` fails (branch collision, dirty state), report the error, do
**not** launch the job, and suggest the fix (e.g., `git worktree prune`).

---

## Section 7 — Build the Delegate Prompt

Load `references/delegate-prompt.md`, substitute `{{TASK}}` with the resolved task
text, and write the result to `$SD/prompt.txt`.

---

## Section 8 — Launch + Poll (spec §5 steps 3–4)

### 8.1 Launch

```bash
# Record the actual launch workspace before launching (ws.txt is used by orphan cancel)
echo "$WS" > "$SD/ws.txt"
JOBID=$(bash ~/.agents/skills/_shared/scripts/launch-job.sh "$WS" "$SD" \
         $([ "$MODE" = write ] && echo --write) --effort "$EFFORT" \
         ${MODEL:+--model "$MODEL"} \
         "$(cat "$SD/prompt.txt")")
```

`launch-job.sh` runs `codex task --background --fresh`, parses the job-id, retries
until `logFile` is non-null, writes `$SD/jobid.txt` and `$SD/logfile.txt`, and
echoes the job-id. `MODEL` is set only when the user passed `--model`; when unset,
the `${MODEL:+…}` expansion omits the flag entirely and Codex uses its runtime default.

### 8.2 Poll (background)

Start the poller with `run_in_background: true` so CC is not blocked:

```bash
# 20-min cap inlined as a literal — shell vars (like the §5.1 POLL_TIMEOUT constant)
# do NOT persist between Bash tool calls, and an unset var would make the cap 0 = unbounded.
POLL_TIMEOUT_SECS=1200 \
  bash ~/.agents/skills/_shared/scripts/poll-job.sh "$WS" "$JOBID" "$SD/status.txt"
```

CC continues other work. The harness notifies when the poller exits (i.e., when the
Codex job reaches a terminal state: `completed`, `failed`, or `cancelled`; or when
`POLL_TIMEOUT` minutes elapse).

**On timeout:** `$SD/status.txt` contains `timeout`. CC must:
1. Cancel the job: `bash ~/.agents/skills/_shared/scripts/codex.sh "$WS" cancel "$JOBID"`
2. Report the timeout to the user.
3. Offer retry.

See also §12 "Poller times out" row.

When `--wait` is explicitly given, instead of backgrounding, run `poll-job.sh` in
the foreground and wait for it to return before proceeding to evaluation.

---

## Section 9 — Batch (spec §5)

A **batch** is triggered when the task input is a list — multiple newline- or
`;`-separated task lines (slash form), or several distinct tasks named in one NL
request.

Protocol:

1. Split the input on `;` and/or newlines to produce an ordered list of task lines.
2. Per-line flags are allowed (e.g., one line `--write`, another read-only); a
   leading flag with no per-line override applies to all.
3. Fan out: one job per task (each gets its own SLUG, statedir, worktree if needed).
4. Enforce `MAX_CONCURRENT=4` jobs in flight. When the queue exceeds 4, wait for the
   next job to reach a terminal state before launching the next one.
5. **Pipeline, not barrier:** evaluate each job *as it lands*. Early finishers
   integrate while slower ones still run. Do not wait for all jobs before starting
   evaluation.
6. Write one `registry.jsonl` entry per job; track each independently.

---

## Section 10 — Evaluate on Completion (spec §6)

When the poller notifies that a job has completed, execute this evaluation sequence:

### 10.1 Fetch result

```bash
bash ~/.agents/skills/_shared/scripts/codex.sh "$WS" result "$JOBID" > "$SD/result.md"
```

If `result.md` is empty, treat as failure → diagnostics path (see Section 12).

### 10.2 Write tasks — follow `references/evaluate-write.md`

1. **Verify** — run the verify command **in the worktree** (`$WS`). Explicit
   `--verify` wins; else infer the project's test/build command. If you cannot infer
   it, run a lighter compile/build check **and say so** — never silently claim
   "verified". Capture output to `$SD/verify.log`.

2. **Grade** — Did tests/build pass? Does the diff from
   `worktree.sh diff "$REPO" "$SLUG"` actually satisfy the task intent (not merely
   compile)?

3. **Decide:**
   - **PASS** → integrate: call `worktree.sh apply "$REPO" "$SLUG"`. This brings
     the diff into the main working tree as **unstaged** changes (never auto-commits).
     A **non-zero apply exit = conflict** — CC resolves it; surface non-trivial
     conflicts to the user; never discard.
   - **Tests ran and failed** → retry up to `MAX_RETRIES=1`, re-delegating with the
     failure log as added context; then fallback (CC finishes it or surfaces to user).
   - **Verify command could not run** (missing tool, environment error) → surface
     this explicitly; do NOT claim "verified". Distinguish from a genuine test
     failure.

### 10.3 Read-only tasks — follow `references/evaluate-readonly.md`

### 10.4 Write verdict

Write `$SD/verdict.md` recording: grade (pass/fail), decision taken, verify output
summary, and any user-visible notes.

---

## Section 11 — Cleanup (spec §5 step 8)

After successful integration:

```bash
bash ~/.agents/skills/subcodex/scripts/worktree.sh remove "$REPO" "$SLUG"
```

This removes the worktree dir and the `subcodex/$SLUG` branch. The statedir
(`$SD/`) is retained for the retention window (newest 10 job dirs) so recent
history — task, status, logfile paths — stays inspectable after the run.

For read-only tasks there is no worktree to remove; skip this step.

---

## Section 12 — Failure Handling (spec §8)

| Failure | Handling |
|---|---|
| Preflight: codex not authed | Stop; tell user to run `/codex:setup`. No job launched. |
| Job status `failed`/`cancelled` | `result` returns nothing — read logfile, abort job, show diagnostics, offer retry of just that job. |
| Job launch: no job-id parsed (exit 71) | Read `$SD/launch.log` for raw codex output; offer retry. |
| Poller times out (> `POLL_TIMEOUT` min) | Cancel job, report, offer retry. |
| Empty result | Treat as failure → same diagnostics path. |
| `--write` in non-git dir | Non-git refusal: offer read-only or explicit in-place-with-warning on user confirm. |
| Worktree add fails (branch collision, dirty) | Report, don't launch; suggest fix. |
| Merge-back conflict | CC resolves (never discards); non-trivial → surface to user. |
| Verify *command* errors (vs tests failing) | Distinguish: tests-failed → retry with context; couldn't-run → surface, never claim "verified". |
| User Ctrl+C mid-flight | Background Codex jobs keep running; next invocation reads `registry.jsonl`, cancels non-terminal jobs (orphan reconciliation). |

---

## Section 13 — Full Lifecycle (quick reference)

```
/subcodex [--write] [--verify "cmd"] <task>

  0. Disambiguation check (§1.2) → classify or ask
  0. Confirm-before-launch gate (§2) → echo + wait for inferred forms
  0. Preflight: bash ~/.agents/skills/_shared/scripts/codex-preflight.sh || stop
  0. Match effort (§3) + cancel orphans (§5.5) + sweep old state dirs (§5.4)
  1. Register: mkdir $STATE_ROOT/$SLUG; write task/mode/verify/effort/prompt;
     append registry.jsonl
  2. --write → worktree.sh add $REPO $SLUG  ⇒ WS = worktree path
     read-only →                              WS = $REPO
  3. launch-job.sh "$WS" "$SD" [--write] --effort "$EFFORT" [--model "$MODEL"] "$(cat $SD/prompt.txt)"
       ⇒ saves jobid + logfile; echoes JOBID
  4. poll-job.sh "$WS" "$JOBID" "$SD/status.txt"  [run_in_background: true]
     CC keeps working; harness notifies on poller exit
  ▼ (notify)
  5. fetch: codex.sh result $JOBID → $SD/result.md
  6. EVALUATE (§10): write → evaluate-write.md; read-only → evaluate-readonly.md
  7. DECIDE: pass → worktree.sh apply (UNSTAGED) ; fail → retry ≤ MAX_RETRIES else fallback
  8. cleanup: worktree.sh remove; write $SD/verdict.md
```

---

## Section 14 — Related References

- `references/delegate-prompt.md` — the prompt template handed to Codex (contains
  `{{TASK}}` placeholder). This is the `delegate-prompt` the skill uses.
- `references/evaluate-write.md` — CC's evaluation procedure for write tasks.
- `references/evaluate-readonly.md` — CC's evaluation procedure for read-only tasks.
- `references/help.md` — user-facing `/subcodex` help text.
- `~/.agents/skills/_shared/references/codex-effort-match.md` — effort table.
- `~/.agents/skills/_shared/scripts/launch-job.sh` — job launcher.
- `~/.agents/skills/_shared/scripts/poll-job.sh` — background poller.
- `~/.agents/skills/_shared/scripts/codex-preflight.sh` — auth check.
- `~/.agents/skills/subcodex/scripts/worktree.sh` — worktree add/remove/diff/apply.
