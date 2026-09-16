# clodex

A Claude Code skill that runs a structured multi-round dialectic between this Claude
session and a parallel Codex job, producing a single synthesized "settled" answer
plus a per-decision attribution footer.

**Use it for:** hard architectural questions, library/framework choices, debugging
strategies, design tradeoffs — anything where a 5–35 min adversarial second opinion
is worth the wall-clock cost.

**Don't use it for:** simple factual questions, syntax lookups, or anything you'd
get a confident answer to from a single model in 30 seconds. The dialectic protocol
exists to surface and resolve genuine disagreement; if there's no disagreement to
resolve, you're paying for theater.

---

## Quick start

After Claude Code is running with the `clodex` skill loaded, invoke it either way:

```bash
# Slash form — explicit query
/clodex Should we migrate the API gateway from Express to Fastify?

# Natural-language form — Claude infers the query and confirms before launching
"can you review the code over clodex"
"have clodex weigh in on the auth refactor"
"clodex this design"
```

Both forms run the same protocol. The natural-language form adds one short
*"Inferred clodex query: '…' — proceed?"* check before launching, since the query
has to be extracted from your message + recent conversation context.

---

## Invocation reference

### Slash form

```
/clodex [--effort low|medium|high|xhigh] [--rounds N] <query text>
```

Examples:

```
/clodex Should I use Pydantic v2 or attrs for this data model?
/clodex --effort xhigh Compare these two database schemas for migration safety
/clodex --rounds 5 Architectural review: should our event bus be Kafka or NATS?
/clodex --effort high --rounds 4 Should we adopt SolidJS for the new dashboard?
```

### Natural-language form

Any message containing the word "clodex" triggers the skill. Examples that work:

```
can you review the code over clodex
have clodex weigh in on the auth refactor
use clodex on the typer/click question
clodex this design
settle this with clodex
review the code over clodex (running 5 rounds)
clodex this with high effort and 4 rounds
```

Claude extracts the query, effort, and rounds from your message + conversation,
then asks you to confirm:

```
Inferred clodex query: "Review the auth/oauth.ts file for token refresh races"
Rounds: 5     (default 3, range 3–5)
Effort: high  (auto-matched to Claude model: Opus)

Proceed? (yes / edit query / cancel)
```

---

## Protocol pipeline

Shape of a single clodex invocation (default behaviour, `--rounds 3` + revise ON):

**`propose → critique → revise → synthesize`**

```
R1: *Propose*                              (parallel, independent)
    claude_proposal
    codex_proposal
R2: *Critique* the other's proposal        (parallel, anonymous)
    claude_critique                      (of codex_proposal)
    codex_critique                       (of claude_proposal)
R2.5: *Revise* own proposal using critique received  (parallel)
    claude_revised = claude (claude_proposal + codex_critique)
    codex_revised  = codex  (codex_proposal  + claude_critique)
R3: *Synthesize*                           (Claude only)
    claude_revised                       (artifact being judged)
    codex_revised                        (artifact being judged)
    claude_critique                      (context)
    codex_critique                       (context)
```

With `--no-revise` the R2.5 step is skipped and R3 judges between the
first-draft proposals instead of the revised ones — equivalent to the prior
3-stage `propose → critique → synthesize` shape:

```
R1: Propose      → claude_proposal, codex_proposal
R2: Critique     → claude_critique, codex_critique
R3: Synthesize   → judges between claude_proposal vs codex_proposal,
                   with both critiques as context
```

For `--rounds 4` or `--rounds 5`, additional *re-critique* rounds run between
R2 and R2.5 (each side re-critiques the other's most-recent critique). The
*Revise* step still runs once, after the last critique round, using each
side's most-recent critique-of-them as input.

---

## Flags

### `--effort`

Codex reasoning depth. **Default: auto-matched to Claude's active model**
(Opus → `high`, Sonnet → `medium`, Haiku → `low`). An explicit `--effort` flag
overrides the matched default.

| Level    | Wall-clock per round | When to use |
|----------|----------------------|-------------|
| `low`    | 10–60s               | Quick triage; Haiku-matched default |
| `medium` | 1–3 min              | Everyday questions; Sonnet-matched default |
| `high`   | 2–5 min              | Substantive questions; Opus-matched default |
| `xhigh`  | 5–15 min             | Architectural decisions, deep review |

**Never `minimal`** — returns HTTP 400 with Codex's tool config (image_gen and
web_search aren't allowed at minimal effort).

**Why auto-match?** The dialectic compares answers from Claude and Codex. If
Codex is on `high` while Claude is on Sonnet/Haiku, Codex is over-resourced
relative to Claude, and synthesis's "whose argument is sharper?" judgments tend
to favour Codex for compute reasons rather than capability reasons. Matching
keeps the comparison apples-to-apples. Override explicitly if you want an
asymmetric config (e.g. for calibration experiments).

### `--rounds`

Total round count. Default `3`. Valid range `3–5`.

| N | Structure | Total wall-clock (with `--effort high`, revise ON) |
|---|---|---|
| 3 | R1 propose, R2 critique, R2.6 revise, R3 synth | ~6–17 min (default — cost-quality sweet spot) |
| 4 | R1 propose, R2 critique, R3 re-critique, R3.6 revise, R4 synth | ~11–28 min |
| 5 | R1 propose, R2 critique, R3 re-critique, R4 re-critique, R4.6 revise, R5 synth | ~16–38 min |

Hard cap is 5. Below 3 is degenerate (no debate happens). Values outside the range
are clamped, with a warning shown.

**Convergence guard:** before each new critique round (rounds 3+), Claude checks
whether the prior round surfaced new contested points or just restated old ones. If
just restating, the protocol exits early to synthesis — better to ship a clean
answer than spin on hair-splitting.

### `--no-revise`

Disable the Step 2.6 self-revision round. Revision is **ON by default**: after
critique completes, each side rewrites its own R1 using the critique it
received, BEFORE synthesis judges. Synthesis then chooses between refined R1s,
not first drafts.

| Mode | Synthesis judges between | Wall-clock added |
|---|---|---|
| Default (revise ON) | revised R1s (each side absorbed landed critique points) | +30s–2min |
| `--no-revise` (revise OFF) | original first-draft R1s + critiques as context | 0 |

Use `--no-revise` when wall-clock matters more than answer quality (quick second
opinions, well-bounded questions both models likely agree on, or time-critical
decisions). Default ON because A/B testing on representative codebases showed
material quality lift — particularly on questions with architectural patterns
that benefit from each side absorbing the other's critique before judgment.

The self-revision mechanism is inspired by Du et al. 2024 (ICML),
[*"Improving Factuality and Reasoning in Language Models through Multiagent
Debate"*](https://openreview.net/pdf?id=zj7YuTE4t8) — adapted from their
symmetric peer-update pattern into clodex's `propose → critique → revise → judge`
architecture (the 4-stage shape that replaced the prior 3-stage `propose →
critique → judge` once Step 2.6 became the default).

---

## What the output looks like

After the protocol completes, you'll see a structured response with:

```
═══ clodex DIALECTIC COMPLETE (3 rounds) ═══

Inspect Codex sessions in another terminal:
  R1:  codex resume <uuid>
  R2:  codex resume <uuid>
State preserved at: /tmp/clodex-state/<timestamp>

═══ FINAL SETTLED ANSWER ═══

[the synthesized answer with embedded [decision: who won] annotations]

## Decision Log
- <Contested point>: <winner> — <one-line why>
- <Contested point>: <winner> — <one-line why>
- ...

═══ STATS ═══
  Attribution: Claude (25.0%)  |  Codex (37.5%)  |  Agreed (37.5%)
  Time taken:  Claude (131s)    |  Codex (42s)
```

The attribution footer is the protocol's verdict on whether it was worth running:

- **Common >70%** → both AIs would have said similar things. A single-model query
  would have been cheaper.
- **Common <30%** → genuine divergence. The dialectic earned its wall-clock cost.
- **Skewed Claude/Codex** → one model was meaningfully sharper on this question.
  Useful calibration over time about which model fits which question type.

---

## Watching the protocol live

While the dialectic is running, you'll see Claude's reasoning in your Claude Code
session. To watch Codex's side:

```bash
# In another terminal — tail the live log of any Codex job
tail -f /tmp/codex-companion/<workspace-hash>/jobs/<job-id>.log

# After a Codex round completes — attach to its full session interactively
codex resume <session-id-from-result>
```

The exact `tail -f` command is printed by clodex right after launching each Codex
job. The exact `codex resume` commands are printed in the final-answer header.

---

## File layout

```
~/.agents/skills/clodex/
├── README.md                            ← this file (human-readable user guide)
├── SKILL.md                             ← machine-readable orchestration spec
└── references/
    ├── help.md                          ← help block shown for `/clodex` with no query
    ├── round1-prompt.md                 ← framing for the R1 proposal
    ├── round2-prompt.md                 ← framing for the R2 cross-critique
    ├── round-recritique-prompt.md       ← framing for R3+ re-critique (only when --rounds ≥ 4)
    ├── revision-prompt.md               ← framing for Step 2.6 self-revision (default ON)
    ├── stats-format.md                  ← exact format rules for the STATS block
    └── synthesis-prompt.md              ← framing for the final synthesis

~/.claude/skills/clodex                  ← symlink → ~/.agents/skills/clodex
```

State for each invocation lives at `/tmp/clodex-state/<timestamp>/`. Each invocation
produces:

- `query.txt`, `effort.txt`, `rounds.txt`, `cwd.txt` — invocation parameters
- `r1-launch.log`, `r1-jobid.txt`, `r1-logfile.txt`, `r1-status.txt`, `r1-codex.md` — round 1 artifacts
- `r2-codex-prompt.md`, `r2-launch.log`, `r2-jobid.txt`, `r2-logfile.txt`, `r2-status.txt`, `r2-codex.md` — round 2 artifacts
- ... (one set per Codex round)

**Retention policy.** The skill keeps the **newest 10** state dirs and auto-purges
older ones at the start of every new clodex invocation. So your most recent run is
always available for inspection (read the artifacts, `codex resume <id>`, etc.) until
you launch the next one — at which point only the newest-10 survive. To change the
retention count, edit the `tail -n +11` in Step 0.2 of `SKILL.md`.

You can `ls /tmp/clodex-state/` anytime to see your retained runs.

---

## Configuration

The skill auto-detects everything and has no config file. It reads:

- The Codex companion script, resolved dynamically via the shared wrapper
  `~/.agents/skills/_shared/scripts/codex.sh` (which globs the newest installed version
  under `~/.claude/plugins/cache/openai-codex/codex/`)
- Your authenticated Codex CLI session (via `codex login`)

If either is missing, clodex stops at preflight and tells you the fix.

---

## Troubleshooting

### "Inferred query doesn't match what I meant"

Choose `edit query` at the confirmation prompt, type the query you want, then proceed.
Or use the slash form for unambiguous queries: `/clodex <exact query>`.

### Codex job appears "missing" in `codex:status`

Codex tracks jobs **per workspace directory**. If you launched from one folder and
query status from another, the job won't appear. The skill handles this internally
(always queries from the original `cwd`), but if you're checking manually, `cd` to
the same folder first.

### "Codex r1 ended in failed"

The skill aborts the protocol and points you at `/tmp/clodex-state/<ts>/r1-error.log`
for diagnostics. Common causes:
- **Sandbox blocked the credential read — the usual cause, and it is NOT expiry.**
  Claude Code's sandbox denies `Read(./**/auth.json)`, and codex stores its token
  at `~/.codex/auth.json`. Codex inherits that sandbox when Claude Code spawns it,
  so it cannot read its own credential. `codex doctor` reports it as
  `✗ auth · Operation not permitted (os error 1)`, and the `✗ reachability` and
  `⚠ websocket` lines below it are downstream symptoms of the same thing — the
  network is fine. Re-running `codex login` does not help, and running it from
  inside Claude Code hits the identical wall. Confirm with
  `codex doctor 2>&1 | grep -E 'auth|reachability'` in your own terminal: `✓ auth`
  there plus `✗ auth` inside Claude Code pins it on the sandbox.

  **Fixed (2026-08-19)** by allowing that one path through the sandbox — the
  settings key is `sandbox.filesystem.allowRead`, which takes precedence over
  both `denyRead` and the harness baseline. Restart Claude Code after changing
  it. Claude Code cannot apply this itself: the auto-mode classifier blocks an
  agent from widening its own credential access, so the edit has to be made by
  hand.

  ⚠️ Trade-off accepted when enabling it: anything in Claude Code's Bash process
  tree can then read the ChatGPT OAuth token, not only codex. The
  `permissions.deny` rule `Read(./**/auth.json)` still blocks the dedicated Read
  tool, so that layer of defence survives.
- Codex CLI auth genuinely expired — run `codex login` **in your own terminal**.
  Only suspect this after the check above shows `✗ auth` in your terminal too.
- Network blip during the Codex job — just retry the clodex invocation.

### "sandbox_apply: Operation not permitted" / Codex can't read the repo

Distinct from the auth failure above — auth is green and Codex still reports it
cannot read anything. Cause: Codex applies its **own** macOS seatbelt profile for
`read-only` / `workspace-write` modes, and macOS refuses to nest that inside
Claude Code's sandbox. Every read is rejected and the round returns nothing
useful.

**Locally patched (2026-08-19)** in the vendor companion
`~/.claude/plugins/cache/openai-codex/codex/<ver>/scripts/codex-companion.mjs` —
both `sandbox:` assignments (review path and task path) set to
`danger-full-access`, each with an inline comment explaining why. Claude Code's
sandbox remains the outer containment, so the posture is unchanged: the repo is
readable but **not** writable — verified by having Codex attempt a write, which
returned `DENIED — operation not permitted` with no file created.

⚠️ **This patch is in a plugin cache directory and a plugin update will revert
it silently.** The symptom on reversion is exactly the message above. Re-apply
by setting both `sandbox:` values back to `danger-full-access`. Check with:

```bash
grep -n 'sandbox: ' ~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs
```

Two `danger-full-access` lines = patched. Any `read-only` / `workspace-write`
means the update reverted it.

### `codex doctor` shows `✗ reachability` — usually ignorable

`✗ reachability` does **not** mean clodex is broken, and it is not a symptom of the
auth problem above (it persists after auth goes green). It reports the auxiliary
endpoints — codex's own MCP transport (`chatgpt.com/backend-api/ps/mcp`), the
model-list refresh (`/backend-api/codex/models`), and any local MCP server such as
browseros-neo on `127.0.0.1:9010`. The completion API those jobs actually run on is
unaffected; a `codex exec` probe returns normally with `✗ reachability` showing.

Those failures surface as `ERROR rmcp::transport::worker: worker quit with fatal:
Transport channel closed` lines on stderr. They are noise, not failure — but they
land in `r1-error.log`, so don't read their presence there as the cause of a failed
round. The real gate is `bash $CODEX_SH <dir> setup --json | jq -e '.ready'`.

### Protocol seems to never finish

Each round has a polling loop with no built-in timeout. If a Codex job hangs
(rare), you can manually cancel it from any terminal:

```bash
bash ~/.agents/skills/_shared/scripts/codex.sh <workspace-cwd> cancel <job-id>
```

`<workspace-cwd>` is the directory the job was launched in (printed when the round
launches). The shared wrapper resolves the companion dynamically, so it works across
Codex version bumps.

The job-id is printed when the round launches.

### "Common attribution is always >80%, dialectic feels redundant"

You're using clodex for questions that don't have meaningful divergence between the
two models. Switch to a single-model query for these types. Save clodex for genuinely
contested questions — architectural decisions, library choices with real tradeoffs,
debugging stuck problems where a different perspective might help.

---

## Design notes

- **3 rounds is the default for a reason.** Beyond ~3 critique rounds, AI-debate
  research shows diminishing returns: round 1 establishes positions, round 2 surfaces
  real critiques, round 3 settles. Rounds 4+ tend toward hair-splitting unless the
  question is genuinely deep.
- **Self-revision (Step 2.6) is the default.** Without revision, synthesis judges
  between two *first-draft* R1s — if a critique exposes a fixable flaw, the
  originator never got to fix it, so synthesis marks them down on a flaw revision
  would have closed. Step 2.6 lets each side rewrite its own R1 in light of the
  critique it received, BEFORE synthesis judges. A/B tests on two representative
  codebases showed material quality lift (cleaner top-of-funnel, contested
  findings verified during revision, larger "Agreed" attribution as both sides
  absorb each other's critique points). Mechanism inspired by Du et al. 2024
  (ICML), [*"Improving Factuality and Reasoning in Language Models through
  Multiagent Debate"*](https://openreview.net/pdf?id=zj7YuTE4t8) — adapted from
  their symmetric peer-update to clodex's `propose → critique → revise → judge`
  shape. Use
  `--no-revise` to skip and save ~30s–2min wall-clock when answer quality is
  less critical than turnaround time.
- **Synthesis-by-judge beats convergence-by-debate.** Forcing two AIs to literally
  agree is unreliable (sycophancy, oscillation). Having Claude judge the contested
  points with both sides' arguments in front of it produces better answers and is
  what the protocol actually does — `--rounds 5` doesn't mean "loop until they
  agree", it means "give them more critique rounds before Claude judges".
- **Bias control: the critic doesn't know who wrote the answer.** All cross-critique
  prompts say *"another AI proposed this"* rather than naming Claude or Codex. This
  prevents brand-based deference or dismissal in the critique.
- **Smart retention of state dirs.** The newest 10 `/tmp/clodex-state/<ts>/`
  directories are preserved as audit breadcrumbs; older ones are auto-purged at
  the start of every new clodex run. The just-finished run is always available
  for inspection until you launch the next one. This balances "I want to revisit
  recent results" against `/tmp/` accumulating dozens of stale dirs over time.

---

## Version

This skill was built and tested in 2026-04. Verified end-to-end on `/clodex --rounds
3 --effort low` runs. The `--rounds 4/5` paths are implemented but less heavily
tested in production — file an issue if you hit unexpected behavior.
