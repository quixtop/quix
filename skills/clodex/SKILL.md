---
name: clodex
author: shrix
description: (shrix) Multi-round Claude+Codex dialectic (default 3 rounds, max 5) — propose, cross-critique, synthesize. Panel mode (`/clodex --panel`, "run a panel on X", "get a multi-model review of X") instead has several DIFFERENT models answer independently, critique once, and an evidence-based judge rule (it runs the tests for code); same-model panels are refused. ONLY when the user explicitly asks, e.g. "/clodex <query>", "use clodex on X", "settle this with clodex" — or when /code-audit's design lens invokes the default mode (owner's standing authorization). Not on incidental mentions, meta-questions about the skill, or code containing the word.
---

# clodex — Claude+Codex multi-round dialectic (default 3, configurable to 5)

## Invocation modes

This skill supports **two equally valid invocation patterns**:

**A. Explicit slash form** — `/clodex <query text>`
- The query is the literal text after `/clodex`.
- Use this when the query is self-contained and unambiguous.

**B. Natural-language form** — an explicit request that uses "clodex" as an action (Path C)
- Examples: "can you review the code over clodex", "have clodex weigh in on this",
  "clodex this design", "settle this with clodex", "use clodex on the auth refactor".
- The query must be **inferred from the user's message + recent conversation context**.
- See "Step 0a — Resolve the query" below. **Confirm the inferred query with the
  user before launching** the dialectic — a 6–38 min protocol on a misunderstood
  question wastes time and tokens.

## Panel mode (`--panel`) — a different procedure

`/clodex --panel …`, "run a panel on X" or "get a multi-model review of X" →
READ `~/.agents/skills/clodex/references/panel.md` and follow it. It is the
whole procedure: several different models, one cross-critique, a neutral judge,
no convergence loop. Nothing below this section applies to panel mode — no
rounds, no revision, no synthesis — and nothing in it changes the default
dialectic below.

## Optional flags (work in either invocation mode)

- `--effort low|medium|high|xhigh` — Codex reasoning effort. Default
  auto-matched to Claude's active model by the shared effort table; see the
  Step 0a pre-step. Explicit flag overrides the match.
  - **Never use `--effort minimal`** — returns HTTP 400 with Codex's tool config.
- `--no-revise` — disable the Step 2.6 self-revision round. Revision is ON by
  default (each side revises its own R1 using the critique it received before
  synthesis judges). `--no-revise` skips Step 2.6 entirely; synthesis judges
  between first-draft R1s. Use when wall-clock matters more than answer
  quality. (Paper attribution + design rationale: see README.md design notes.)
- `--rounds N` — total round count. Default `3`. Valid range `3–5`.
  - `N=3`: R1 propose, R2 critique, R3 synth (default; cost-quality sweet spot).
  - `N=4`: R1 propose, R2 critique, R3 re-critique, R4 synth.
  - `N=5`: R1 propose, R2 critique, R3 re-critique, R4 re-critique, R5 synth.
  - **Hard cap: 5.** Beyond that, returns clamp the value to 5 and warn the user
    (do not error). Below 3 is degenerate (no debate happens) — clamp to 3, warn.
  - Each extra round adds ~5–10 min wall-clock + ~doubles token cost per pair.
  - **Convergence guard:** before launching each extra round k (k ≥ 3), check if the most
    recent critique round just restated prior contested points without surfacing
    new ones. If so, **skip remaining critique rounds and jump to synthesis early**
    — better to ship a clean answer than spin on hair-splitting. (See
    references/extra-rounds.md.)

## Protocol (parameterized by N = `--rounds`, default 3)

```
Round 1     (parallel):   Claude proposes  ║  Codex proposes
Round 2     (parallel):   Claude critiques Codex r1  ║  Codex critiques Claude r1
Round 3..N-1 (parallel):  Each side re-critiques the OTHER's most-recent critique
                          (only runs when N ≥ 4; uses the re-critique template)
Step 2.6    (parallel):   Each side revises its OWN R1 using the critique it received
                          (DEFAULT ON; skipped if --no-revise). See revision-prompt.md.
Round N     (Claude):     Synthesize final settled answer + attribution footer
                          (judges from REVISED R1s if Step 2.6 ran; from
                          first-draft R1s if --no-revise)
```

Total wall-clock by N (with `--effort high`, revise ON which is the default):
- N=3: ~6–17 min  (default; subtract ~30s–2min with `--no-revise`)
- N=4: ~11–28 min
- N=5: ~16–38 min

## Constants

```
CODEX_SH=~/.agents/skills/_shared/scripts/codex.sh
```

`CODEX_SH` is the **shared** wrapper (also used by subcodex): it resolves the newest installed codex companion dynamically (robust to plugin version bumps — no hardcoded version), cds into the workspace, and runs it — collapsed into one allowlistable pattern. Invoke as `bash $CODEX_SH <workspace-dir> <subcommand> [args...]` for `result`, `status` and `cancel`.

The readiness check, every launch and every poll go through the shared scripts
beside it — the same ones subcodex calls, each running `codex.sh` itself:

- `~/.agents/skills/_shared/scripts/codex-preflight.sh` — is Codex authed and ready (Step 0.1).
- `~/.agents/skills/_shared/scripts/launch-job.sh` — starts the background Codex task (always `--fresh`), prints only its job-id, writes `jobid.txt`, `logfile.txt` and `launch.log` into the job dir it is given. Exit 71 / 72 / 73 → see Failure handling.
- `~/.agents/skills/_shared/scripts/poll-job.sh` — polls the job every 2 s and writes ONE terminal status into a file: `completed` · `failed` · `cancelled` · `timeout` (still running at its cap, default 20 min) · `missing` (Codex no longer knows the job — several polls in a row found nothing).

Each Codex job has its own **job dir** in the run's state dir: `$STATE_DIR/r1/`,
`$STATE_DIR/r2/`, … and `$STATE_DIR/revise/` — `launch-job.sh` writes there and
`poll-job.sh` writes `status.txt` there. Clodex's own files (prompts, results,
timing marks) stay flat in `$STATE_DIR`.

## Step 0a — Resolve the query and parameters (or show help)

**Pre-step: detect Claude's active model and compute `MATCHED_EFFORT`.**

This runs *before* the path dispatch below, because Path B and Path C consume
`MATCHED_EFFORT` when the user did not supply an explicit `--effort` flag.

**Effort matching** — read from `~/.agents/skills/_shared/references/codex-effort-match.md`
(the table clodex shares with subcodex). The effort it gives for your model is
`MATCHED_EFFORT`.

The `MATCHED_EFFORT` value is the *default* Codex effort for this run. An
explicit `--effort` flag (slash-form or natural-language) still overrides it —
this only changes what the default is when no flag is given. Reason: keep the
dialectic apples-to-apples; if Claude is on Sonnet/Haiku, Codex on `high` would
be over-resourced and skew "who's sharper" judgments in synthesis.

If detection fails (no model line found, unrecognised model name), set
`MATCHED_EFFORT=high` and tell the user:
`warning: could not detect Claude model — defaulting Codex to high. Comparison may not be apples-to-apples.`

Remember the detected model name; Step 0.3 will persist it to
`$STATE_DIR/claude-model.txt` once `$STATE_DIR` exists.

**Three routing decisions in this order:**

### Path A — Help mode (no query / explicit help request)

Trigger this path when ANY of these is true:

- Slash-form input is exactly `/clodex` (no arguments at all).
- Slash-form input contains `-h` or `--help` (as the only non-flag arg)
  with no other query text.
- Slash-form input has flags like `--rounds 5` but no query text after the flags
  — except `--panel`: a bare `/clodex --panel` infers its query (§ Panel mode),
  never help.
- An explicit clodex request has **no extractable query AND no clear
  conversation topic to infer from** (e.g., the user types "clodex" alone). A
  meta-question ("how do I use clodex") is answered normally, without invoking.

**Action:** Read `~/.agents/skills/clodex/references/help.md` and show its inner
help block (the part inside the triple backticks) to the user verbatim. Do NOT run
preflight, do NOT launch any Codex job. Skill exits cleanly. The user will re-invoke
with a real query.

### Path B — Slash-form invocation with query (`/clodex [--effort X] [--rounds N] <query>`)

- Parse `--effort`, `--rounds`, and `--no-revise` flags directly from the slash
  arguments.
- If the parsed effort is `minimal`, warn the user and use `low` instead —
  `minimal` is a documented hard failure (HTTP 400) with Codex's tool config.
- If `--effort` was not provided in the slash args, set it from `MATCHED_EFFORT`
  computed in the Step 0a pre-step above.
- If `--no-revise` is NOT in the slash args, `REVISE=yes` (default on).
  If `--no-revise` IS present, `REVISE=no`.
- Remaining text is `$QUERY` verbatim.
- Skip the confirmation prompt below; the user was explicit.
- Continue to Step 0 (preflight + state setup).

### Path D — Invoked by `/code-audit` (owner's standing authorization, 14Aug26)

`/code-audit`'s design-challenge lens may invoke clodex without the user asking
in that message — the one exception to the user-only rule. The audit supplies the
query (its adversarial mandate), so skip the confirmation in Step 0a and run
review-only: never fix, never edit. Every other gate in this skill still applies,
including the Step 0.1 readiness check (`codex-preflight.sh`, which runs
`codex setup --json`). This authorization covers the DEFAULT
dialectic only — never panel mode, which runs only on the user's own request.

### Path C — Natural-language invocation (only EXPLICIT action requests with "clodex")

This path runs ONLY when the user uses "clodex" as an action verb in a request to
invoke the skill — e.g. "use clodex on X", "review this over clodex", "have clodex
weigh in", "settle X with clodex", "clodex this design". Do NOT activate this path
for incidental mentions ("I read about clodex", "what does clodex do", code or
files containing the word "clodex"). When in doubt, do not invoke; ask the user
first if they want to clodex it.

1. **Extract the candidate query** from the user's message + last few conversation turns.
   Common patterns:
   - "review the code [over clodex]" → query is "Review <the code most recently
     discussed in this conversation> for X" — identify what code from context.
   - "have clodex weigh in on X" → query is X with surrounding context.
   - "use clodex on the auth refactor" → query is "Propose an approach for the
     auth refactor we discussed", with relevant prior context appended.

2. **Extract `--rounds N` from natural language.** Look for these patterns
   (case-insensitive, integer N):
   - "running N rounds" / "with N rounds" / "do N rounds"
   - "N-round" / "N round dialectic" / "N round debate"
   - "go N rounds" / "N rounds of clodex"
   - Default to N=3 if no count mentioned.
   - Clamp: if N<3, set N=3 and note this in the confirmation. If N>5, set N=5
     and note this in the confirmation.

3. **Extract `--effort` from natural language.** Look for:
   - "with low/medium/high/xhigh effort"
   - "deep" / "thorough" → suggest `high` or `xhigh`
   - "quick" / "fast" → suggest `low`
   - If the user asked for `minimal`, warn and use `low` instead — `minimal` is a
     documented hard failure (HTTP 400) with Codex's tool config.
   - Default to `MATCHED_EFFORT` (from the Step 0a pre-step) if no hint.

3a. **Extract `--no-revise` from natural language.** Look for these patterns
   (case-insensitive) to set `REVISE=no`:
   - "no revise" / "skip revise" / "without revision"
   - "no revision" / "skip the revision step"
   - Default to `REVISE=yes` if no hint (revision is the default behaviour).

4. **Confirm with the user before proceeding.** Format:
   ```
   Inferred clodex query: "<your inferred query>"
   Rounds: <N>     (default 3, range 3–5)
   Effort: <level> (auto-matched to Claude model: <model_name>; override with --effort)
   Revise: <yes|no> (default yes; --no-revise to skip)

   Proceed? (yes / edit query / cancel)
   ```
   Wait for confirmation. The 6–38 min cost makes a 10-second clarification cheap.

5. Once confirmed, the inferred-and-approved values become `$QUERY`, `$N`, `$EFFORT`
   for Step 0+.

## Step 0 — Preflight + retention sweep + state setup

Run once. If any check fails, stop and tell the user with the fix.

**0.1 Preflight checks:**

1. `bash ~/.agents/skills/_shared/scripts/codex-preflight.sh` — Codex authed and
   ready? It runs `codex setup --json` in `/tmp` (setup doesn't depend on cwd) and
   checks `.ready`. Exit 1 → not authed: tell the user to run `/codex:setup`.
   70 (no Codex companion — its ✗ line says how to install one) or 73 / 77 (the
   Codex data dir is unsafe) → relay its ✗ line.
2. `bash ~/.agents/skills/_shared/scripts/state-root.sh /tmp/clodex-state` — private state root.

**0.2 Retention sweep** (smart cleanup of older state dirs):

```bash
# Keep the newest 10 state dirs; runs at START, so the last run stays inspectable.
# Glob [0-9]* targets timestamp-named dirs created by this skill and never matches
# anything else in /tmp/clodex-state/. To change retention count, edit the `+11`.
# find, not ls: -type d excludes SYMLINKS. /tmp is world-writable, and
# `rm -rf link/` follows the link and deletes its TARGET — a local user planting
# /tmp/clodex-state/9999999999 -> anywhere gets arbitrary deletion.
# Names must be ALL digits (-regex, then the grep): a planted dir whose name holds
# a newline ("1<newline>victim") would otherwise split into a relative path that
# rm resolves against the user's project. `--` stops a name being read as a flag;
# errors are NOT silenced, because a sweep failing forever while reporting success
# is worse than one that complains.
find -E /tmp/clodex-state -mindepth 1 -maxdepth 1 -type d -regex '/tmp/clodex-state/[0-9]+' \
  -exec stat -f '%m %N' {} + 2>/dev/null | grep -E '^[0-9]+ /tmp/clodex-state/[0-9]+$' \
  | sort -rn | tail -n +11 | cut -d' ' -f2- | tr '\n' '\0' | xargs -0 -r rm -rf --
```

This is intentionally lazy (cleanup at start of next run, not end of current).
Reason: the just-finished run stays inspectable until you launch the next one.

**0.3 Init state for this run:**

```bash
INVOKE_CWD=$(pwd)
STATE_DIR="/tmp/clodex-state/$(date +%s)"
mkdir -p "$STATE_DIR"
echo "$INVOKE_CWD" > "$STATE_DIR/cwd.txt"
```

Save the user's query, effective effort, round count, revision flag, and
detected Claude model using the **Write tool** (not heredoc — handles
multi-line cleanly):
- Write `$STATE_DIR/query.txt` with the raw query.
- Write `$STATE_DIR/effort.txt` with the *effective* effort level (matched
  default or user override).
- Write `$STATE_DIR/rounds.txt` with the round count N as an integer (default `3`,
  clamped to `[3, 5]`).
- Write `$STATE_DIR/revise.txt` with `yes` (default) or `no` (if `--no-revise`).
- Write `$STATE_DIR/claude-model.txt` with the detected Claude model name from
  the Step 0a pre-step (or `unknown` if detection failed).

Tell user (literal output, four lines):

    Detected Claude: <model_name>
    Matched Codex effort: <MATCHED_EFFORT>  (effective effort: <EFFORT>)
    Self-revision (Step 2.6): <REVISE>
    clodex dialectic starting: rounds=$N, effort=$EFFORT, revise=$REVISE, state=$STATE_DIR

## Step 1 — Round 1 (single response turn)

Do all three of the following in the **same** Claude response.

**1a. Launch Codex r1 in background** (also capture start timestamp for Claude timing):

```bash
date +%s > "$STATE_DIR/r1-tstart.txt"
bash ~/.agents/skills/_shared/scripts/launch-job.sh "$INVOKE_CWD" "$STATE_DIR/r1" \
  --effort "$(cat "$STATE_DIR/effort.txt")" "$(cat "$STATE_DIR/query.txt")"
```

It prints the job-id (`R1_JOBID`), and its status line names the log file
(`R1_LOG`; ⚠ instead of ✓ when the log is not known yet, and `logfile.txt` then
reads `null`); both are on disk as `$STATE_DIR/r1/jobid.txt` and
`$STATE_DIR/r1/logfile.txt`. The raw `codex task` output is in `$STATE_DIR/r1/launch.log`.
A non-zero exit launched nothing trackable — Failure handling, launch row.

Tell the user **exactly**:

```
═══ ROUND 1 ═══
Codex r1 launched: <R1_JOBID>
Watch live in another terminal:  tail -f <R1_LOG>
```

**1b. In the same response, produce Claude's own round-1 answer:**

Read `~/.agents/skills/clodex/references/round1-prompt.md` for framing. Apply it to
the query in `$STATE_DIR/query.txt`. Be specific, name tradeoffs, don't hedge. Output
the answer in conversation — it stays in context for synthesis. No need to save to disk.

**1c. Start the round-1 poller** using Bash with `run_in_background: true`:

```bash
date +%s > "$STATE_DIR/r1-tclaude.txt"   # marks end of Claude's r1 text turn
POLL_TIMEOUT_SECS=1800 bash ~/.agents/skills/_shared/scripts/poll-job.sh "$INVOKE_CWD" \
  "$(cat "$STATE_DIR/r1/jobid.txt")" "$STATE_DIR/r1/status.txt"
```

You'll be notified by the harness when this background job exits.
`$STATE_DIR/r1/status.txt` then holds one terminal status (see Constants).

**Note on status JSON shape:** A `status <jobid> --json` query wraps the job in
`.job.*`. A workspace-wide `status --json` (no job-id) uses top-level `.running[]`
and `.recent[]`. Easy to mix up.

## Step 2 — Round 2 (after R1 poller notifies)

When the R1 poller completes, in the next turn:

**2a. Fetch Codex r1 result (or handle failure):**

```bash
R1_STATUS=$(cat "$STATE_DIR/r1/status.txt")
if [ "$R1_STATUS" = "completed" ]; then
  bash $CODEX_SH "$INVOKE_CWD" result "$(cat "$STATE_DIR/r1/jobid.txt")" \
    > "$STATE_DIR/r1-codex.md"
else
  # failed/cancelled/timeout/missing — read the log file for diagnostics (`result` returns "No job found")
  R1_LOG=$(cat "$STATE_DIR/r1/logfile.txt" 2>/dev/null)   # may be "null" when the job never logged
  if [ -f "$R1_LOG" ]; then tail -50 "$R1_LOG" > "$STATE_DIR/r1-error.log"
  else echo "no Codex log file (logfile: ${R1_LOG:-none})" > "$STATE_DIR/r1-error.log"; fi
  # ABORT the protocol. Tell user:
  #   "Codex r1 ended in $R1_STATUS, see $STATE_DIR/r1-error.log. Aborting dialectic."
fi
```

Read `$STATE_DIR/r1-codex.md` so Codex's r1 answer is in your context.

**2b. Build round-2 prompt for Codex (Codex critiquing Claude's r1):**

Use the **Read tool** on `~/.agents/skills/clodex/references/round2-prompt.md`. The
template has placeholders `{{QUERY}}` and `{{OTHER_AI_ANSWER}}`. In your head, substitute:
- `{{QUERY}}` ← contents of `$STATE_DIR/query.txt`
- `{{OTHER_AI_ANSWER}}` ← Claude's r1 answer from earlier in this conversation

Use the **Write tool** to save the assembled prompt to `$STATE_DIR/r2-codex-prompt.md`.

**2c. Launch Codex r2 in background** (also capture start timestamp):

```bash
date +%s > "$STATE_DIR/r2-tstart.txt"
bash ~/.agents/skills/_shared/scripts/launch-job.sh "$INVOKE_CWD" "$STATE_DIR/r2" \
  --effort "$(cat "$STATE_DIR/effort.txt")" "$(cat "$STATE_DIR/r2-codex-prompt.md")"
```

`R2_JOBID` and `R2_LOG` as in 1a, from `$STATE_DIR/r2/`.

Tell user:

```
═══ ROUND 2 ═══
Codex r2 (critique) launched: <R2_JOBID>
Watch live:  tail -f <R2_LOG>
```

**2d. In the same response, produce Claude's round-2 critique of Codex's r1:**

Apply the same `round2-prompt.md` framing (steelman first, then attack) to Codex's r1
answer (which is now in `$STATE_DIR/r1-codex.md` and in your context). Don't propose
your own alternative — critique only. Output in conversation.

**2e. Start the round-2 poller** — same pattern as 1c, with `run_in_background: true`:

```bash
date +%s > "$STATE_DIR/r2-tclaude.txt"   # marks end of Claude's r2 critique turn
POLL_TIMEOUT_SECS=1800 bash ~/.agents/skills/_shared/scripts/poll-job.sh "$INVOKE_CWD" \
  "$(cat "$STATE_DIR/r2/jobid.txt")" "$STATE_DIR/r2/status.txt"
```

## Step 2.5 — Additional critique rounds (only when N ≥ 4)
With the default 3 rounds, go straight to Step 2.6. When `N ≥ 4`, READ
`references/extra-rounds.md` and run it before Step 2.6.

## Step 2.6 — Self-revision (default ON; skipped if `--no-revise`)

Each side rewrites its own R1 using the critique another AI wrote about that
R1, BEFORE synthesis judges. Synthesis then chooses between refined answers,
not first drafts. (See README.md design notes for paper attribution + the
empirical rationale for this being the default.)

**2.6.0 Skip check.** Read `$STATE_DIR/revise.txt`. If `no`, skip this entire
section and go directly to Step 3.

**2.6a. Persist Claude's last critique to disk for Codex revision input.**

Codex needs Claude's R2 critique (or the last critique-round Claude wrote, when
N ≥ 4) as a stable artifact. Use the **Write tool** to save the relevant Claude
critique text from conversation to `$STATE_DIR/r2-claude.md` (use `r{M}-claude.md`
naming if N ≥ 4 and M is the last critique round Claude wrote).

**2.6b. Build Codex revision prompt.**

Use the **Read tool** on `~/.agents/skills/clodex/references/revision-prompt.md`.
Substitute:
- `{{QUERY}}` ← contents of `$STATE_DIR/query.txt`
- `{{YOUR_ORIGINAL_ANSWER}}` ← `$STATE_DIR/r1-codex.md`
- `{{CRITIQUE_OF_YOU}}` ← `$STATE_DIR/r2-claude.md` (or `r{M}-claude.md`)

Use the **Write tool** to save the assembled prompt to
`$STATE_DIR/revise-codex-prompt.md`.

**2.6c. Launch Codex revision in background + start poller.**

```bash
date +%s > "$STATE_DIR/revise-tstart.txt"
bash ~/.agents/skills/_shared/scripts/launch-job.sh "$INVOKE_CWD" "$STATE_DIR/revise" \
  --effort "$(cat "$STATE_DIR/effort.txt")" "$(cat "$STATE_DIR/revise-codex-prompt.md")"
```

`REVISE_JOBID` and `REVISE_LOG` as in 1a, from `$STATE_DIR/revise/`.

Tell user:

```
═══ STEP 2.6 — SELF-REVISION ═══
Codex revising r1: <REVISE_JOBID>
Watch live:  tail -f <REVISE_LOG>
```

**2.6d. In the same response, produce Claude's revised R1.**

First make sure Codex's most-recent critique is ON DISK: if
`$STATE_DIR/r{M}-codex.md` does not exist yet (with the default 3 rounds, M = 2
and nothing has fetched it), wait for that round's poller to write a terminal
`r{M}/status.txt`, then fetch it with the Step 3a command. Step 3a later skips
the fetch because the file exists. Never revise against a critique you have not
read.

Apply the same `revision-prompt.md` framing to Claude's own R1 (in conversation)
plus Codex's most-recent critique of Claude (`$STATE_DIR/r{M}-codex.md`).
Produce a revised version of Claude's R1.

Use the **Write tool** to save Claude's revised R1 to
`$STATE_DIR/r1-claude-revised.md` so synthesis can re-read it as a stable
artifact (symmetric with Codex's revised R1 on disk).

**2.6e. Start the revision poller** using Bash with `run_in_background: true`:

```bash
date +%s > "$STATE_DIR/revise-tclaude.txt"   # marks end of Claude's revision turn
POLL_TIMEOUT_SECS=1800 bash ~/.agents/skills/_shared/scripts/poll-job.sh "$INVOKE_CWD" \
  "$(cat "$STATE_DIR/revise/jobid.txt")" "$STATE_DIR/revise/status.txt"
```

When the poller fires with `completed` in `$STATE_DIR/revise/status.txt`, fetch
Codex's revised R1:

```bash
bash $CODEX_SH "$INVOKE_CWD" result "$(cat "$STATE_DIR/revise/jobid.txt")" \
  > "$STATE_DIR/r1-codex-revised.md"
```

If the status is anything else (`failed`, `cancelled`, `timeout`, `missing`),
fall back to using the original R1s for synthesis (treat as if `--no-revise`
was set) and warn the user that revision failed so synthesis is judging from
first drafts.

## Step 3 — Synthesis (after final critique round notifies)

**3a. Fetch the most-recent Codex critique result** (if not already fetched in Step 2.5):

```bash
# Let M = the last critique round (M = N-1 normally, or earlier if convergence aborted)
bash $CODEX_SH "$INVOKE_CWD" result "$(cat "$STATE_DIR/r{M}/jobid.txt")" \
  > "$STATE_DIR/r{M}-codex.md"
```

Read every `$STATE_DIR/r*-codex.md` file so all of Codex's contributions are in context.

**If `REVISE=yes` and Step 2.6 ran successfully**, also read both revised R1s:
- `$STATE_DIR/r1-codex-revised.md` (already fetched at end of Step 2.6)
- `$STATE_DIR/r1-claude-revised.md` (saved by Claude in Step 2.6d)

**3b. Synthesize using `references/synthesis-prompt.md`:**

Use the **Read tool** on `~/.agents/skills/clodex/references/synthesis-prompt.md`.
You now have all artifacts in your context:
- Claude's r1 proposal (in conversation)
- Codex's r1 proposal (`$STATE_DIR/r1-codex.md`)
- Claude's critique rounds 2 through M (in conversation; `r{k}-claude.md` on disk if Step 2.6 persisted them)
- Codex's critique rounds 2 through M (`$STATE_DIR/r2-codex.md` … `$STATE_DIR/rM-codex.md`)
- **If `REVISE=yes`:** Claude's revised R1 (`$STATE_DIR/r1-claude-revised.md`) and
  Codex's revised R1 (`$STATE_DIR/r1-codex-revised.md`)

Where M is the last critique round actually run (N-1 in the normal case, or earlier
if Step 2.5's convergence guard aborted). For N=3, M=2.

The template decides what is judged (revised R1s when both exist, else the
first drafts) and the decision-log shape; just provide the full set of
artifacts in your context, then produce ONE final settled answer per its rules. The attribution
math (Step 3c) counts decisions across ALL critique rounds — a point Codex raised in
round 4 still counts as Codex-raised, not as having lower weight than a round-2 point.

**3c. Compute Stats (attribution + timing):**

Two computations, both shown in the final Stats block.

**Attribution (3-bucket method):** while doing the decision log in 3b, classify every
meaningful decision in the final answer into one of three buckets:

| Bucket | Definition |
|---|---|
| **Common** | Both r1s converged on this (substantive agreement, not coincidence). |
| **Claude** | Claude won this contested point (claude r2 critique landed) OR claude raised this gap that ended up in the final. |
| **Codex**  | Codex won this contested point (codex r2 critique landed) OR codex raised this gap that ended up in the final. |

Each decision counts equally. Compute:

```
total      = common + claude + codex
common_pct = round(100 * common / total, 1)
claude_pct = round(100 * claude / total, 1)
codex_pct  = round(100 * codex  / total, 1)
```

Rounding may sum to 100.1 / 99.9 — that's fine.

**Time taken (model reasoning time only — not wall-clock):**

For each round actually run (k = 1 to last critique round M):

- **Claude per-round time** = `r{k}-tclaude.txt - r{k}-tstart.txt` (in seconds)
- **Codex per-round time** = `.job.elapsed` from status JSON (strip `s` suffix to int)

Sum each side across all rounds:

```bash
claude_total=0
codex_total=0
for k in $(seq 1 $M); do
  if [ -f "$STATE_DIR/r${k}-tstart.txt" ] && [ -f "$STATE_DIR/r${k}-tclaude.txt" ]; then
    t0=$(cat "$STATE_DIR/r${k}-tstart.txt")
    t1=$(cat "$STATE_DIR/r${k}-tclaude.txt")
    claude_total=$((claude_total + (t1 - t0)))
  fi
  if [ -f "$STATE_DIR/r${k}/jobid.txt" ]; then
    jid=$(cat "$STATE_DIR/r${k}/jobid.txt")
    elapsed_str=$(bash $CODEX_SH "$INVOKE_CWD" status "$jid" --json 2>/dev/null | \
                  jq -r '.job.elapsed // .job.duration // "0s"')
    # elapsed reads "45s", "2m 5s" or "1h 2m 3s" — sum every unit into seconds
    elapsed_int=$(printf '%s' "$elapsed_str" | grep -oE '[0-9.]+[hms]?' | \
                  awk '{v=$0+0; if ($0 ~ /h$/) v*=3600; else if ($0 ~ /m$/) v*=60; t+=v} END {printf "%d", t}')
    codex_total=$((codex_total + ${elapsed_int:-0}))
  fi
done

# Add the Step 2.6 self-revision step's time when revision ran. Both files exist
# only when REVISE=yes and the revision job didn't fail; absent on --no-revise
# runs and on revision failure.
if [ -f "$STATE_DIR/revise-tstart.txt" ] && [ -f "$STATE_DIR/revise-tclaude.txt" ]; then
  t0=$(cat "$STATE_DIR/revise-tstart.txt")
  t1=$(cat "$STATE_DIR/revise-tclaude.txt")
  claude_total=$((claude_total + (t1 - t0)))
fi
if [ -f "$STATE_DIR/revise/jobid.txt" ]; then
  jid=$(cat "$STATE_DIR/revise/jobid.txt")
  elapsed_str=$(bash $CODEX_SH "$INVOKE_CWD" status "$jid" --json 2>/dev/null | \
                jq -r '.job.elapsed // .job.duration // "0s"')
  elapsed_int=${elapsed_str%s}
  codex_total=$((codex_total + elapsed_int))
fi
```

Note: `claude_total` measures Claude's **per-round inline reasoning** (R1 propose +
R2 critique + R3+ re-critique). It does NOT include the synthesis turn itself
(synthesis time is not measured separately; treat it as ~30s of additional Claude
work but don't add it to the reported number). Honest under-report by design.

**3d. Extract Codex resume session-ids and present the final answer:**

Each `$STATE_DIR/r*-codex*.md` file ends with lines like
`Codex session ID: <uuid>` and `Resume in Codex: codex resume <uuid>`. Extract one
UUID per Codex job actually run (one per critique round + one for revision if
Step 2.6 ran).

Present the final answer to the user formatted EXACTLY as:

```
═══ clodex DIALECTIC COMPLETE (<actual_rounds> rounds<revise_note><convergence_note>) ═══

Inspect Codex sessions in another terminal:
  R1:      codex resume <uuid-1>
  R2:      codex resume <uuid-2>
  ... (one per Codex critique round actually run)
  Revise:  codex resume <uuid-revise>     (only if Step 2.6 ran)
State preserved at: $STATE_DIR

═══ FINAL SETTLED ANSWER ═══

<the synthesized answer with embedded decision-log lines>

═══ STATS ═══
  Attribution: Claude (<claude_pct>%)  |  Codex (<codex_pct>%)  |  Agreed (<common_pct>%)
  Time taken:  Claude (<claude_total>s)    |  Codex (<codex_total>s)
```

**Stats block + header rendering:** before producing the final answer block, **read
`~/.agents/skills/clodex/references/stats-format.md`** for the exact format rules
(label spacing, separator widths, value formatting, header rendering for the
`DIALECTIC COMPLETE` line). The Stats block is mandatory on every clodex run.

## Step 4 — Cleanup

```bash
# Defensive: cancel any non-terminal Codex jobs (no-op if already terminal)
for jid in $(cat "$STATE_DIR"/*/jobid.txt 2>/dev/null); do
  bash $CODEX_SH "$(cat $STATE_DIR/cwd.txt)" cancel "$jid" 2>/dev/null
done
```

**Do NOT delete `$STATE_DIR` here.** The just-finished run stays available for
inspection until the next `/clodex` invocation. State-dir purging happens lazily
via the **Step 0.2 retention sweep** (keeps newest 10 dirs, auto-purges older at
the start of every new run). This way you can always re-read or `codex resume`
the most recent run without it vanishing prematurely.

## Critical reminders (most-bitten gotchas)

1. **Always pass `$INVOKE_CWD` as the workspace** — to `launch-job.sh`,
   `poll-job.sh` and `bash $CODEX_SH "$INVOKE_CWD" <subcmd>` alike — and never call
   the codex companion directly. Job state is workspace-scoped, so a call from
   another dir makes the job appear "missing"; the wrapper also keeps the operation
   allowlistable as one pattern.
2. **Always `--fresh`**, never `--resume` — `launch-job.sh` always passes it. Each
   round needs independent reasoning.
3. **In round-2 prompts, frame as "another AI proposed X"**, never "Claude proposed X" —
   prevents brand-based bias in Codex's critique.
4. **If `$INVOKE_CWD` is not a git repo**, Codex still works but may be more ephemeral.
   Warn the user but proceed.

## Failure handling

| Failure | Action |
|---------|--------|
| Preflight check fails | Stop. Tell user the exact fix (`/codex:setup`, etc.). |
| Launch exit 71 / 72 / 73 (`launch-job.sh`) | Nothing trackable launched. Act on its ✗ line — 71 means a job may still be running untracked: find it in `status --json` (`.running[]`) and cancel it before any retry. Offer retry of just that round. |
| Codex round status = `failed`, log shows a temporary error (`Reconnecting`, stream disconnected, rate limit / 429, 5xx, timed out) | Tell the user, wait 60 s, relaunch THAT round once with the same inputs. Fails again → the row below. |
| Codex round status = `failed` (any other cause, e.g. auth, invalid request — or the one retry also failed) | Read logFile, abort, present diagnostics, offer retry of just that round. |
| Poller times out (30 min: clodex passes `POLL_TIMEOUT_SECS=1800`, since xhigh rounds take 5–15 min — status `timeout`) | Cancel job, tell user, offer retry. |
| Job vanished (status `missing`) — Codex stopped answering for it (5 failed polls, ~10 s) | It may still be running: `cancel` its id first (a no-op if it is gone), then tell the user and offer a retry of just that round. |
| Codex returns empty result | Treat as failure. Same diagnostics path. |
| User Ctrl+C mid-flight | Background Codex jobs continue — run cleanup (Step 4) on next interaction to cancel them. |
