---
name: panel
author: shrix
description: "(shrix) Adversarial multi-model panel — N agents from DIFFERENT models independently propose, cross-critique once, and are judged on evidence. Heterogeneity is enforced: same-model panels are refused and redirected to clodex's self-revision, because the research shows they underperform their cost. For code, the judge runs the tests rather than weighing arguments. Triggers on /panel [query], 'run a panel on X', 'get a multi-model review of X'. NOT for delegating work (subcodex) or a two-party dialectic (clodex)."
metadata:
  version: "1.0"
  category: workflow
---

# panel — Adversarial Multi-Model Review

## Meaning
`panel` answers "what do several DIFFERENT models, thinking in deliberately
different ways, conclude about this — and where do they disagree?"

It is not a vote and not a consensus engine. It surfaces independent positions,
has them attack each other exactly once, then judges on evidence. Disagreement
is the product, not a problem to resolve.

## Not this skill
- **clodex** — two-party Claude+Codex dialectic, converges toward synthesis.
- **subcodex** — delegates a task to a worker; no debate.
- `panel` is for when you want SEVERAL models and want the disagreement visible.

## Why heterogeneity is enforced, not encouraged
The evidence is one-sided and the design obeys it:

| finding | source | consequence here |
|---|---|---|
| model heterogeneity is the decisive factor | MAD/2502.08788 | single-model panels REFUSED |
| self-correction beats homogeneous debate | Cost of Consensus | redirect to `clodex --revise` |
| deliberative consensus scored **76%** vs 83% independent, *below every single model* | Roundtable/2509.16839 | **no convergence loop, ever** |
| error correlation r=0.53–0.69 across models | Roundtable | agreement is weak evidence; say so |
| personas over identical reasoning = fixed mental set | DMAD | lenses are METHODS, not roles |
| naive judging is sycophancy-prone | 2510.12697 | judge scores grounded claims only |

⚠️ These come from reasoning benchmarks (GSM8K-style), not design review. Strong
priors, not proof — say so when reporting a panel's conclusion.

## Grammar

    vendor : model : effort @ job = lens × count

Only `vendor:model` is required.

    /panel --agents codex:gpt-5.6-sol:max, cc:opus, gemini:pro:medium
    /panel --agent cc:opus:max@critique=attack-assumptions --agent codex:gpt-5.6-sol

⚠️ **Model ids are the VENDOR's own, verbatim — and the vendors disagree about
aliases.** Verified by launching both:

| vendor | family alias | must use |
|---|---|---|
| `cc` | ✅ `opus` resolves to the latest Opus | alias or pinned id |
| `codex` | 🔴 **no aliases** — `sol` returns HTTP 400 | full slug always |

Codex slugs live in `~/.codex/models_cache.json`: `gpt-5.6-sol`, `gpt-5.6-terra`,
`gpt-5.6-luna`, `gpt-5.5`, `gpt-5.4`. A plausible shorthand (`sol`, `sol5.6`) is
rejected at launch. Read the cache rather than guessing.

⚠️ **Consequence for reproducibility.** `cc:opus` is a MOVING target — CC's docs
say aliases "update over time", and `opus` already shifted from 4.8 once. So two
panels a month apart may have had different participants with nothing saying so.
Report the RESOLVED model in the verdict's configuration block, never the alias
the user typed. When a panel's result will be cited later, pin both sides.

- Separators: `,` with any whitespace · `=` or `/` for lens · `×` or `*` for count
- `--agent` repeatable; `--agents` takes the comma list; identical meaning
- Omitted effort → vendor default · omitted lens → `auto` · omitted count → 1
- ⚠️ Effort vocabulary is the VENDOR's, passed through verbatim. Never normalise
  across vendors — `medium` on one is not `medium` on another, and pretending
  otherwise makes runs look comparable when they are not.

## Three entry points
| form | for |
|---|---|
| `/panel <query>` | presets — one pick, then run |
| `/panel --pick` | widget builder; assembles the grammar and sends it |
| `/panel --agents …` | explicit, for repeat runs |

Presets exist so the DEFAULT path cannot produce the homogeneous configuration
the research says underperforms.

## Step 0 — Resolve the query and the configuration

### 0a. Where the query comes from
| invocation | query |
|---|---|
| `/panel <text>` | the literal text |
| `/panel` (bare) | **INFER from the conversation** |
| "run a panel on X" | X, plus surrounding context |

**Bare `/panel` infers.** Read back over the recent conversation and identify
what is actually being decided or disputed — the open design question, the
disagreement, the thing just built that wants attack. Then state it back:

    Panel on: "<inferred query>"
    (from: <one line on what in the conversation this came from>)

⚠️ **Confirm before launching.** A panel is 5–13 model calls; an inferred query
that misses the point wastes all of them. If nothing in the conversation reads
as a question worth debating, say so and ask rather than inventing one.

### 0b. Recommend a configuration from the problem
When the user supplies a problem description, ANALYSE it and propose a
configuration rather than making them choose blind. Classify on three axes:

| axis | read from | drives |
|---|---|---|
| **kind** | code · design · debugging · research · judgement call | lenses, jobs |
| **difficulty** | novelty, branching, how wrong a wrong answer is | effort |
| **breadth** | how many independent facets it has | agent count |

Mapping — these have a defensible basis:

    code        → one @verify agent, execution-first lens; judge RUNS it
    debugging   → reason-backwards, attack-assumptions
    design      → steelman-opposite, cheapest-sufficient, analogy-prior-art
    research    → analogy-prior-art, first-principles, one @research agent
    judgement   → steelman-opposite + attack-assumptions; expect no verdict

    difficulty: routine → default effort · hard → xhigh · irreversible → max
    breadth:    single question → 2 agents · 3+ facets → 3-4

⚠️ **Recommend models for DIVERSITY, never for aptitude.** Effort, lens, job and
count follow from the problem; the model set follows only from "use every vendor
that has an adapter." There is no evidence that any vendor is better at code, or
at design, and asserting one would be superstition presented as analysis. If
asked why a model was chosen, the honest answer is "because it differs from the
others", not "because it is good at this".

Present the recommendation with its reasoning, then let the user take it,
adjust it, or open the widget:

    Panel on: "<query>"
      kind: design · difficulty: hard · breadth: 2 facets
      → 2 agents, xhigh effort — this is reversible, so not max
      → lenses: steelman-opposite, cheapest-sufficient
      codex:gpt-5.6-sol:xhigh=steelman-opposite
      cc:opus:xhigh=cheapest-sufficient
    [run] [adjust] [pick manually]

### 0c. Configuration — interactive when unspecified
Bare `/panel` (or `--pick`) resolves the agent set INTERACTIVELY. Two forms,
same outcome — a valid `--agents` string:

1. **Widget** (preferred on Desktop) — `show_widget` builder: one row per agent
   with model, job, lens, effort and count dropdowns, a live diversity meter,
   and a Run button that `sendPrompt`s the assembled grammar back. The user
   never types the grammar.
2. **Interactive questions** (CLI, or when a widget would not render) —
   `AskUserQuestion` with the presets as options, then one follow-up only if
   they choose Custom. Keep it to two questions; a long interrogation costs
   more attention than the panel saves.

Presets, offered first in both forms:

| preset | agents | when |
|---|---|---|
| **Default dyad** | `cc:opus:xhigh, codex:gpt-5.6-sol:medium` | ✅ **the default** |
| **Deep dyad** | same models at `max` | irreversible calls |
| **Balanced trio** | dyad + `gemini:pro:high` | when the adapter exists |
| **Wide panel** | trio + `cc:sonnet:high` | more coverage |
| Custom | → widget or grammar | |

**The default panel is `cc:opus:xhigh, codex:gpt-5.6-sol:medium`.** Two vendors,
so the heterogeneity requirement is met by construction, and the asymmetric
effort is deliberate — differing reasoning depth is itself a source of
divergence, so it costs less than two `max` agents and diverges more than two
identical ones. The user may override model, job, effort or count on either.

⚠️ **Deep dyad is the default**, not the trio: it is the only preset whose every
vendor has a working adapter today. Presets naming `gemini` render disabled with
that reason until one is built.

⚠️ Presets containing a vendor with no adapter are shown but disabled, with the
reason. Never offer what cannot launch.

### 0d. State setup
```bash
# -H excludes symlinks: /tmp is world-writable, and `rm -rf link/` follows the
# link and deletes its TARGET. -print0/-0 survives odd names. `--` stops a name
# being read as a flag. Errors are NOT silenced — a sweep that fails forever
# while reporting success is the failure mode this replaced.
find /tmp/panel-state -mindepth 1 -maxdepth 1 -type d -name '[0-9]*' \
  -exec stat -f '%m %N' {} + 2>/dev/null | sort -rn | tail -n +11 | cut -d' ' -f2- \
  | tr '\n' '\0' | xargs -0 -r rm -rf --
STATE_DIR="/tmp/panel-state/$(date +%s)"; mkdir -p "$STATE_DIR"
printf '%s\n' "$QUERY" > "$STATE_DIR/query.txt"
printf '%s\n' "$AGENTS" > "$STATE_DIR/agents.txt"
```
Retention sweep runs FIRST, so the previous run stays inspectable until now.

## Phases — exactly three, no loop

### Phase 1 — Independent proposal
Every agent (unless pinned `@critique`) answers the query alone.
- **Agents MUST NOT see each other's work.** Contaminating this destroys the
  independent signal that makes the whole thing work.
- Launch all agents concurrently; one adapter call each.

**Execution.** Slots are `a1…aN` in the order given; a `×N` token expands to N
consecutive slots sharing a model but never a lens.

```bash
# per agent — build the prompt, then dispatch on vendor
Read references/round1-prompt.md → substitute {{QUERY}}, {{LENS}}
Write  "$STATE_DIR/$SLOT-p1.txt"
bash scripts/agent-launch.sh "$STATE_DIR" "$SLOT" "$TOKEN" "$STATE_DIR/$SLOT-p1.txt"
```
- exit 0 → codex job launched; collect later
- **exit 3 → `cc` agent**: spawn with the **Agent tool**, `subagent_type:
  general-purpose`, passing the same prompt file's content. Run it in the
  background so all agents are in flight together, and write its return to
  `$SLOT/result.md` yourself — no shell script can call the Agent tool.
- exit 69 → no adapter. Should be impossible past the gate; abort if seen.

Launch EVERY agent before collecting ANY. Collecting between launches
serialises the phase and multiplies wall-clock by N.

```bash
for SLOT in $SLOTS; do bash scripts/agent-collect.sh "$STATE_DIR" "$SLOT"; done
```
⚠️ A failed agent does NOT abort the panel while ≥2 distinct models remain —
report it and continue. Below 2, abort: a one-model panel is the configuration
this skill refuses.

### Phase 2 — Cross-critique, ONCE
Each agent receives every proposal but its own, and attacks them.
- ⚠️ **There is no round 2 of critique and no convergence check.** Agents state
  positions and stop. Debating to agreement measured *below every single model*
  — the failure mode is persuasive error propagation, where a confidently wrong
  agent flips a correct one.
- Critiques must cite the specific claim being attacked, not summarise.

**Execution.** Same launch/collect shape, one round only:

```bash
# {{OTHERS}} = every OTHER agent's result.md, labelled by slot, never its own
Read references/round2-prompt.md → substitute {{QUERY}}, {{YOUR_ANSWER}}, {{OTHERS}}
Write "$STATE_DIR/$SLOT-p2.txt"
bash scripts/agent-launch.sh "$STATE_DIR" "${SLOT}c" "$TOKEN" "$STATE_DIR/$SLOT-p2.txt"
```
Critique slots are `a1c…aNc`, so phase-1 results stay intact for the judge.
Agents pinned `@propose` are skipped here; `@critique` agents join only here.

### Phase 3 — Judge
The ORCHESTRATOR judges by default: it is the only party that did not compete.
`@judge` may delegate this, at the cost of a participant grading its peers.

**Execution.** Read `references/judge.md` — it is the full procedure, including
the evidence tiers and output shape. Write the ruling to `$STATE_DIR/verdict.md`
before rendering it, so the panel is inspectable after the turn ends.

Scoring rules, in order:
1. **For code — RUN IT.** Tests, build, repro. Execution outranks every
   argument, however well made. A proposal whose tests pass beats one that
   merely reasons well. This is the whole difference between judging code and
   judging prose.
2. Claims grounded in evidence (a file, a run, a citation) outrank assertions.
3. Confidence is NOT evidence. Discount the most assertive voice, not reward it.
4. **Report the minority position.** A dissenting agent may hold the stronger
   argument while the majority repeats one flawed line. Never emit only the
   winner.
5. Agreement is weak evidence — models fail together (r=0.53–0.69). Three
   agreeing agents are not three independent confirmations; say so.

## Lenses — methods, not personas
`auto` (the default) assigns from `references/lenses.md`. A lens says HOW to
think, never WHO to be — a role label over unchanged reasoning still yields a
fixed mental set.

    reason-backwards      start from the failure and work back
    first-principles      rebuild from what must be true
    cheapest-sufficient   find the smallest thing that works
    attack-assumptions    name the load-bearing belief and break it
    steelman-opposite     argue the rejected alternative at full strength
    analogy-prior-art     what already solved this shape of problem

**Assignment rule: spend diversity where model diversity is lowest.** Duplicate
agents of one model have only their lens to differentiate them, so they get
maximally distinct methods. A lone agent of its own model matters less.

⚠️ Never assign a lens by model affinity. There is no evidence that any vendor
is "better at correctness" — that would be superstition dressed as design.

## Jobs — phases by default
Default `all phases`: every agent proposes, then critiques. This works at N=2
and at N=6. Pinning is an override for larger panels:

| job | phases joined | can execute? |
|---|---|---|
| *(default)* | propose + critique | vendor-dependent |
| `@propose` | phase 1 only | — |
| `@critique` | phase 2 only | — |
| `@verify` | phase 2, runs things | **cc only** |
| `@research` | phase 1, gathers prior art | — |
| `@judge` | phase 3, from the orchestrator | — |

⚠️ **Only `cc` agents can execute commands.** Measured: a codex agent asked to
run tests returned `sandbox-exec: sandbox_apply: Operation not permitted` and
correctly downgraded every finding to a hypothesis. Consequences:
- `@verify` and the `execution-first` lens MUST go to a `cc` agent. Assigning
  either to codex produces reasoning labelled as verification, which is the
  exact confusion phase 3 rule 1 exists to prevent.
- On a code query, ensure at least one `cc` agent, or say plainly in the verdict
  that nothing was executed and every claim is a hypothesis.
- A codex agent that says "I could not run this" is behaving CORRECTLY. Do not
  discount it for honesty — discount unexecuted claims presented as findings.

### User-defined jobs
The five above are built in; the list is NOT closed. A custom job is declared
inline and needs two things — which phases it joins, and its prompt:

    @<name>:<phases>          phases ∈ {1,2,3} or a comma set
    /panel --agent cc:opus@devils-advocate:2 \
           --job devils-advocate:2="Argue the panel is asking the wrong
             question entirely. Name the question it should be asking."

- A job joining no phase is an error, not a no-op.
- A job is a ROLE (what you do); a lens is a METHOD (how you think). Both are
  independent and both compose — `@verify=reason-backwards` is coherent.
- Custom jobs are per-invocation. To make one permanent, add it to
  `references/jobs.md` alongside the built-ins.

## Adapters
One seam, two functions: `launch(prompt) → handle`, `collect(handle) → text`.

| vendor | transport | status |
|---|---|---|
| `codex` | `_shared/scripts/launch-job.sh` + `poll-job.sh` | ✅ working |
| `cc` | Agent tool subagent | ✅ working |
| `gemini` | — | 🔴 not built; refuse with that reason |

Never offer a vendor with no adapter. Fail at the gate, not mid-run.

## Guards — checked at the confirm gate
1. **< 2 distinct models → REFUSE.** Say: "a single-model panel underperforms
   self-correction; use `clodex --revise` instead." This is the one hard refusal.
2. Duplicates outnumber distinct models → warn, allow with acknowledgement.
3. Any agent lacking an adapter → refuse, name it.
4. Show the resolved configuration BEFORE launching: every agent, its model,
   effort, job, and the lens `auto` chose. An invisible assignment cannot be
   corrected.
5. Show the launch count. `N agents × 2 phases + 1` — a 6-agent panel is 13
   launches, and MAD frequently loses to cheaper baselines.

## Output
1. **Verdict** — the judged conclusion, with what grounds it.
2. **Dissent** — every position that lost, and why. Never omitted.
3. **Evidence table** — claim · agent · grounded in what · survived critique.
4. **Configuration** — models, lenses, efforts, launch count.
5. State the benchmark caveat when the query was NOT code: these methods are
   validated on reasoning benchmarks, and a design question is not one.

## State
`/tmp/panel-state/<timestamp>/` — per-agent prompt, result, critique, plus
`verdict.md`. Retention: newest 10, swept at the START of the next run.

⚠️ Use `/bin/ls`, never bare `ls` — the shell aliases it to `colorls`, which
returns nothing for these globs and silently skips the sweep.
