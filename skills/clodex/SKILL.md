---
name: clodex
author: shrix
description: (shrix) Multi-round Claude+Codex dialectic (default 3, max 5 rounds). Propose, cross-critique, synthesize. ONLY invoke when the user EXPLICITLY uses clodex as an action — e.g. "/clodex <query>", "use clodex on X", "settle this with clodex". Do NOT trigger on incidental mentions, meta-questions about the skill, or code containing the word.
---

# clodex — Claude+Codex multi-round dialectic (default 3, configurable to 5)

## Invocation modes

This skill supports **two equally valid invocation patterns**:

**A. Explicit slash form** — `/clodex <query text>`
- The query is the literal text after `/clodex`.
- Use this when the query is self-contained and unambiguous.

**B. Natural-language form** — any user message containing "clodex"
- Examples: "can you review the code over clodex", "have clodex weigh in on this",
  "clodex this design", "settle this with clodex", "use clodex on the auth refactor".
- The query must be **inferred from the user's message + recent conversation context**.
- See "Step 0a — Resolve the query" below. **Confirm the inferred query with the
  user before launching** the dialectic — a 5-15 min protocol on a misunderstood
  question wastes time and tokens.

## Optional flags (work in either invocation mode)

- `--effort low|medium|high|xhigh` — Codex reasoning effort. Default
  auto-matched to Claude's active model (Opus→`high`, Sonnet→`medium`,
  Haiku→`low`); see the Step 0a pre-step. Explicit flag overrides the match.
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
  - **Convergence guard:** before launching round k (k ≥ 4), check if the most
    recent critique round just restated prior contested points without surfacing
    new ones. If so, **skip remaining critique rounds and jump to synthesis early**
    — better to ship a clean answer than spin on hair-splitting. (See Step 2e.)

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

`CODEX_SH` is the **shared** wrapper (also used by subcodex) for ALL execution: it resolves the newest installed codex companion dynamically (robust to plugin version bumps — no hardcoded version), cds into the workspace, and runs it — collapsed into one allowlistable pattern. Invoke as `bash $CODEX_SH <workspace-dir> <subcommand> [args...]`.

## Step 0a — Resolve the query and parameters (or show help)

**Pre-step: detect Claude's active model and compute `MATCHED_EFFORT`.**

This runs *before* the path dispatch below, because Path B and Path C consume
`MATCHED_EFFORT` when the user did not supply an explicit `--effort` flag. Read
the "You are powered by the model named X" line from your own system prompt
context. Apply the matching table:

| Detected Claude model | `MATCHED_EFFORT` |
|---|---|
| Opus (any version)   | `high`   |
| Sonnet (any version) | `medium` |
| Haiku (any version)  | `low`    |
| Anything else        | `high` + warn |

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
- Slash-form input has flags like `--rounds 5` but no query text after the flags.
- Natural-language message contains "clodex" but has **no extractable query AND no
  clear conversation topic to infer from** (e.g., user just types "clodex" alone,
  or asks a meta-question like "how do I use clodex" / "what does clodex do").

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
   Wait for confirmation. The 5–35 min cost makes a 10-second clarification cheap.

5. Once confirmed, the inferred-and-approved values become `$QUERY`, `$N`, `$EFFORT`
   for Step 0+.

## Step 0 — Preflight + retention sweep + state setup

Run once. If any check fails, stop and tell the user with the fix.

**0.1 Preflight checks:**

1. `bash $CODEX_SH --resolve-only` — the shared wrapper resolves the codex companion (exits non-zero if none found).
2. `bash $CODEX_SH /tmp setup --json | jq -e '.ready'` — codex CLI authed. (`/tmp`
   is a throwaway workspace arg; setup doesn't depend on cwd.)

**0.2 Retention sweep** (smart cleanup of older state dirs):

```bash
# Keep newest 10 clodex state dirs, purge older. Runs at the START of each new
# invocation so the most-recent run is always available immediately for inspection.
# Glob [0-9]* targets timestamp-named dirs created by this skill and never matches
# anything else in /tmp/clodex-state/. To change retention count, edit the `+11`.
# find, not ls: -type d excludes SYMLINKS. /tmp is world-writable, and
# `rm -rf link/` follows the link and deletes its TARGET — a local user planting
# /tmp/clodex-state/9999999999 -> anywhere gets arbitrary deletion.
# -print0/-0 survives odd names; `--` stops a name being read as a flag; errors
# are NOT silenced, because a sweep failing forever while reporting success is
# worse than one that complains.
find /tmp/clodex-state -mindepth 1 -maxdepth 1 -type d -name '[0-9]*' \
  -exec stat -f '%m %N' {} + 2>/dev/null | sort -rn | tail -n +11 | cut -d' ' -f2- \
  | tr '\n' '\0' | xargs -0 -r rm -rf --
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
bash $CODEX_SH "$INVOKE_CWD" task --background --fresh \
  --effort "$(cat $STATE_DIR/effort.txt)" "$(cat $STATE_DIR/query.txt)" \
  2>&1 | tee "$STATE_DIR/r1-launch.log"
```

Parse and save the job-id and log file path:

```bash
R1_JOBID=$(grep -oE 'task-[a-z0-9]+-[a-z0-9]+' "$STATE_DIR/r1-launch.log" | head -1)
echo "$R1_JOBID" > "$STATE_DIR/r1-jobid.txt"
# logFile is briefly null right after launch; retry up to ~5s
R1_LOG=null
for i in 1 2 3 4 5; do
  R1_LOG=$(bash $CODEX_SH "$INVOKE_CWD" status "$R1_JOBID" --json | jq -r '.job.logFile')
  [ "$R1_LOG" != "null" ] && [ -n "$R1_LOG" ] && break
  sleep 0.5
done
echo "$R1_LOG" > "$STATE_DIR/r1-logfile.txt"
```

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
t0=$SECONDS
until s=$(bash $CODEX_SH "$INVOKE_CWD" status "$(cat $STATE_DIR/r1-jobid.txt)" \
  --json 2>&1 | jq -r '.job.status // "missing"'); \
  [ "$s" = "completed" ] || [ "$s" = "failed" ] || [ "$s" = "cancelled" ]; \
  do [ $((SECONDS - t0)) -ge 1800 ] && { s=timeout; break; }; sleep 2; done
echo "$s" > "$STATE_DIR/r1-status.txt"
```

You'll be notified by the harness when this background job exits.

**Note on status JSON shape:** A `status <jobid> --json` query wraps the job in
`.job.*`. A workspace-wide `status --json` (no job-id) uses top-level `.running[]`
and `.recent[]`. Easy to mix up.

## Step 2 — Round 2 (after R1 poller notifies)

When the R1 poller completes, in the next turn:

**2a. Fetch Codex r1 result (or handle failure):**

```bash
R1_STATUS=$(cat "$STATE_DIR/r1-status.txt")
if [ "$R1_STATUS" = "completed" ]; then
  bash $CODEX_SH "$INVOKE_CWD" result "$(cat $STATE_DIR/r1-jobid.txt)" \
    > "$STATE_DIR/r1-codex.md"
else
  # Failed/cancelled — read the log file for diagnostics (`result` returns "No job found")
  tail -50 "$(cat $STATE_DIR/r1-logfile.txt)" > "$STATE_DIR/r1-error.log"
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
bash $CODEX_SH "$INVOKE_CWD" task --background --fresh \
  --effort "$(cat $STATE_DIR/effort.txt)" "$(cat $STATE_DIR/r2-codex-prompt.md)" \
  2>&1 | tee "$STATE_DIR/r2-launch.log"
R2_JOBID=$(grep -oE 'task-[a-z0-9]+-[a-z0-9]+' "$STATE_DIR/r2-launch.log" | head -1)
echo "$R2_JOBID" > "$STATE_DIR/r2-jobid.txt"
# logFile is briefly null right after launch; retry up to ~5s
R2_LOG=null
for i in 1 2 3 4 5; do
  R2_LOG=$(bash $CODEX_SH "$INVOKE_CWD" status "$R2_JOBID" --json | jq -r '.job.logFile')
  [ "$R2_LOG" != "null" ] && [ -n "$R2_LOG" ] && break
  sleep 0.5
done
echo "$R2_LOG" > "$STATE_DIR/r2-logfile.txt"
```

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

**2e. Start the round-2 poller** — same pattern as 1c, swap r1→r2. The poller's
first line should be `date +%s > "$STATE_DIR/r2-tclaude.txt"` (marks end of
Claude's r2 critique turn for timing).

## Step 2.5 — Additional critique rounds (only when N ≥ 4)

After the R2 poller notifies and you fetch Codex's r2 critique (Step 3a-equivalent
fetching), check the round count `N=$(cat $STATE_DIR/rounds.txt)`. If `N ≤ 3`,
skip this entire section and proceed to Step 2.6 (self-revision) if `REVISE=yes`,
otherwise go directly to Step 3.

If `N ≥ 4`, run a critique loop for `k = 3` to `N-1`, where each round is **a
re-critique that responds to the OTHER side's most-recent critique**. Loop body:

**For each round `k` (k = 3 to N-1):**

**(i) Convergence guard — decide whether to skip remaining rounds.**

Before launching round `k`, judge whether continuing adds value:

- Read both sides' round-(k-1) artifacts (`$STATE_DIR/r{k-1}-codex.md` and Claude's
  in conversation).
- Ask yourself: did round (k-1) surface **substantively new contested points**, or
  did it just restate / nit-pick on points already raised in round 2?
- If **just restating** (no new substantive contested points), **abort the loop
  and proceed to Step 2.6 (self-revision) if `REVISE=yes`, then to synthesis at
  round k** (which becomes the new effective N).
  Tell the user:
  ```
  ═══ EARLY CONVERGENCE (round k-1) ═══
  Critiques are no longer surfacing new contested points. Jumping to synthesis
  at round k instead of round N. (This saves ~5–10 min and produces a cleaner
  final answer than spinning on hair-splitting.)
  ```
- If **new contested points emerged**, continue to (ii).

**(ii) Build re-critique prompts for both sides.**

Read `~/.agents/skills/clodex/references/round-recritique-prompt.md`. The template
has placeholders `{{QUERY}}`, `{{YOUR_PRIOR_CRITIQUE}}`, and `{{OTHER_AI_RESPONSE}}`.

For **Codex's prompt** (Codex re-critiquing — Codex sees Claude's most-recent critique):
- `{{QUERY}}` ← `$STATE_DIR/query.txt`
- `{{YOUR_PRIOR_CRITIQUE}}` ← `$STATE_DIR/r{k-1}-codex.md` (Codex's last critique;
  for k=3 this is the r2 critique)
- `{{OTHER_AI_RESPONSE}}` ← Claude's most-recent critique (in conversation; for k=3
  this is Claude's r2 critique)

Use the **Write tool** to save to `$STATE_DIR/r{k}-codex-prompt.md`.

**(iii) Launch Codex round k in background + start poller.**

Same pattern as Step 2c/2e — replace `r2` with `r{k}`. Job-id, logFile, poller all
named `r{k}-*`. Also save timing markers per the 2c/2e pattern:
- `date +%s > "$STATE_DIR/r{k}-tstart.txt"` at launch
- `date +%s > "$STATE_DIR/r{k}-tclaude.txt"` as the poller's first line

Tell user:

```
═══ ROUND k ═══
Codex r{k} (re-critique) launched: <jobid>
Watch live:  tail -f <logfile>
```

**(iv) In the same response, produce Claude's round-k re-critique.**

Apply the same `round-recritique-prompt.md` framing (concede points the other side
landed; rebut points you disagree with; raise NEW contested points only if genuinely
new). Don't propose your own answer. Output in conversation.

**(v) Wait for Codex round-k poller; fetch result.**

After poller notifies, `bash $CODEX_SH "$INVOKE_CWD" result <jobid> > $STATE_DIR/r{k}-codex.md`.

**End of loop.** When the loop completes (either fully or via early-convergence
abort), proceed to Step 2.6 (self-revision) if `REVISE=yes`, otherwise jump
directly to Step 3.

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
bash $CODEX_SH "$INVOKE_CWD" task --background --fresh \
  --effort "$(cat $STATE_DIR/effort.txt)" "$(cat $STATE_DIR/revise-codex-prompt.md)" \
  2>&1 | tee "$STATE_DIR/revise-launch.log"
REVISE_JOBID=$(grep -oE 'task-[a-z0-9]+-[a-z0-9]+' "$STATE_DIR/revise-launch.log" | head -1)
echo "$REVISE_JOBID" > "$STATE_DIR/revise-jobid.txt"
REVISE_LOG=null
for i in 1 2 3 4 5; do
  REVISE_LOG=$(bash $CODEX_SH "$INVOKE_CWD" status "$REVISE_JOBID" --json | jq -r '.job.logFile')
  [ "$REVISE_LOG" != "null" ] && [ -n "$REVISE_LOG" ] && break
  sleep 0.5
done
echo "$REVISE_LOG" > "$STATE_DIR/revise-logfile.txt"
```

Tell user:

```
═══ STEP 2.6 — SELF-REVISION ═══
Codex revising r1: <REVISE_JOBID>
Watch live:  tail -f <REVISE_LOG>
```

**2.6d. In the same response, produce Claude's revised R1.**

Apply the same `revision-prompt.md` framing to Claude's own R1 (in conversation)
plus Codex's most-recent critique of Claude (from `$STATE_DIR/r2-codex.md` or
`r{M}-codex.md` when N ≥ 4). Produce a revised version of Claude's R1.

Use the **Write tool** to save Claude's revised R1 to
`$STATE_DIR/r1-claude-revised.md` so synthesis can re-read it as a stable
artifact (symmetric with Codex's revised R1 on disk).

**2.6e. Start the revision poller** using Bash with `run_in_background: true`:

```bash
date +%s > "$STATE_DIR/revise-tclaude.txt"   # marks end of Claude's revision turn
t0=$SECONDS
until s=$(bash $CODEX_SH "$INVOKE_CWD" status "$(cat $STATE_DIR/revise-jobid.txt)" \
  --json 2>&1 | jq -r '.job.status // "missing"'); \
  [ "$s" = "completed" ] || [ "$s" = "failed" ] || [ "$s" = "cancelled" ]; \
  do [ $((SECONDS - t0)) -ge 1800 ] && { s=timeout; break; }; sleep 2; done
echo "$s" > "$STATE_DIR/revise-status.txt"
```

When the poller fires, fetch Codex's revised R1:

```bash
bash $CODEX_SH "$INVOKE_CWD" result "$(cat $STATE_DIR/revise-jobid.txt)" \
  > "$STATE_DIR/r1-codex-revised.md"
```

If status is `failed` / `cancelled`, fall back to using the original R1s for
synthesis (treat as if `--no-revise` was set) and warn the user that revision
failed so synthesis is judging from first drafts.

## Step 3 — Synthesis (after final critique round notifies)

**3a. Fetch the most-recent Codex critique result** (if not already fetched in Step 2.5):

```bash
# Let M = the last critique round (M = N-1 normally, or earlier if convergence aborted)
bash $CODEX_SH "$INVOKE_CWD" result "$(cat $STATE_DIR/r{M}-jobid.txt)" \
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

**Choosing what to synthesize FROM** (the key revision-mode distinction):
- If `REVISE=yes` AND both revised R1s exist on disk → synthesis judges between
  the REVISED R1s; the original R1s + critiques are *context for understanding
  what was contested*, not the artifacts being judged.
- If `REVISE=no` OR revision failed → synthesis judges between the original
  first-draft R1s (legacy behaviour).

The synthesis prompt template handles this conditional internally; just provide
the full set of artifacts in your context.

Produce ONE final settled answer per the synthesis template's rules. End with a short
"decision log" of 3–5 contested points and how each was resolved. The attribution
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
  if [ -f "$STATE_DIR/r${k}-jobid.txt" ]; then
    jid=$(cat "$STATE_DIR/r${k}-jobid.txt")
    elapsed_str=$(bash $CODEX_SH "$INVOKE_CWD" status "$jid" --json 2>/dev/null | \
                  jq -r '.job.elapsed // .job.duration // "0s"')
    elapsed_int=${elapsed_str%s}
    codex_total=$((codex_total + elapsed_int))
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
if [ -f "$STATE_DIR/revise-jobid.txt" ]; then
  jid=$(cat "$STATE_DIR/revise-jobid.txt")
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
for jid in $(cat $STATE_DIR/*-jobid.txt 2>/dev/null); do
  bash $CODEX_SH "$(cat $STATE_DIR/cwd.txt)" cancel "$jid" 2>/dev/null
done
```

**Do NOT delete `$STATE_DIR` here.** The just-finished run stays available for
inspection until the next `/clodex` invocation. State-dir purging happens lazily
via the **Step 0.2 retention sweep** (keeps newest 10 dirs, auto-purges older at
the start of every new run). This way you can always re-read or `codex resume`
the most recent run without it vanishing prematurely.

## Critical reminders (most-bitten gotchas)

1. **Always invoke via `bash $CODEX_SH "$INVOKE_CWD" <subcmd>`** — never the codex
   companion directly. Job state is workspace-scoped, so an uncd'd call makes the job
   appear "missing"; the wrapper also keeps the operation allowlistable as one pattern.
2. **Always `--fresh`**, never `--resume`. Each round needs independent reasoning.
3. **In round-2 prompts, frame as "another AI proposed X"**, never "Claude proposed X" —
   prevents brand-based bias in Codex's critique.
4. **If `$INVOKE_CWD` is not a git repo**, Codex still works but may be more ephemeral.
   Warn the user but proceed.

## Failure handling

| Failure | Action |
|---------|--------|
| Preflight check fails | Stop. Tell user the exact fix (`/codex:setup`, etc.). |
| Codex round status = `failed` | Read logFile, abort, present diagnostics, offer retry of just that round. |
| Poller times out (30 min — the loop breaks and writes status `timeout`) | Cancel job, tell user, offer retry. |
| Codex returns empty result | Treat as failure. Same diagnostics path. |
| User Ctrl+C mid-flight | Background Codex jobs continue — run cleanup (Step 4) on next interaction to cancel them. |
