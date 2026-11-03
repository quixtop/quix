# /tune — design decisions

`SKILL.md` holds the procedure and `references/` the detail. This file holds
only WHY the skill is built this way, so the two never become competing
accounts of how it works.

## Scope
Anything Claude Code can read and measure: code and scripts, markdown (docs,
rules, CLAUDE.md, memory, skills, prompts), designs (UI, architecture, APIs),
the Claude Code setup itself, config and infrastructure, data and assets,
processes and the machine. Not limited to text — images, fonts and
spreadsheets are artifacts too, with their own gates.

**One capability:** goal-driven, measured optimization. Bug hunting belongs
to `/rev` and doc–code sync to `/spec` (`CONVENTIONS.md` § Skill
boundaries); `/tune` hands those off rather than duplicating them.

**Named `/tune`, not `/optimize`,** so it never collides with impeccable's
`optimize` command or that package's install record, which claims the
`skills/optimize/` path. The description still says "optimizer" and triggers
on "optimize this", so the word users reach for finds it.

## Decisions and why
| decision | why |
|---|---|
| A written contract before any edit | "better" cannot be redefined after the fact to fit the result |
| One goal metric plus guardrails | a single score becomes a target and gets gamed (Goodhart) |
| Find the constraint first; skip < 5 % | effort on a non-bottleneck is waste; most expert gains sit where agents never look |
| Decline when already at the threshold | past what users perceive, cost exceeds return |
| At most 3 rounds, stop on no gain | a loop without a stop rule spins; self-correction without a signal degrades |
| One hypothesis per change | batched changes make effects impossible to attribute |
| Tests, benchmarks and samples read-only | optimizers learn to pass the check instead of doing the work |
| Adversarial re-check of 2× gains | spectacular gains are most often measurement artifacts |
| Debiased pairwise judge, both orders | models prefer their own writing and polished formatting |
| Must beat a placebo rewrite | a generic "cleaner" rewrite shifts results by suggestion alone |
| A planted worse candidate | a judge that cannot reject it is not judging |
| Held-out samples for prompts, skills, rules | training scores run well above test scores |
| Every number cites its command | agents report gains that never happened |
| Apply inside the project, ask outside | in-project work runs freely, except what reaches outside the machine or cannot be undone; outside the project, security wins |
| Install a guard (a ratchet) | without a standard, gains drift back |
| No population search, no API keys | hundreds of evaluations and external judges do not fit a session |
| A per-profile library, read before diagnosis | without it each run rediscovers what an earlier run already tried; a lesson is re-checked, never trusted, because the earlier target differed |
| Four change verdicts, `confounded` preferred to a guess | a wrong attribution misleads every later run; an honest "cannot tell" does not |
| At most one lesson per entry, or `NO_LESSON` | a lesson the rows do not support is a guess stored as a fact |
| The cheapest form that fixes it | always-on text is paid every turn; a script or on-demand text costs nothing until used |
| A failure seen once is noise | a change aimed at one sample overfits |

## Sources
- GEPA `optimize_anything` — failure feedback over bare scores
- ASRagab/optimize-anything — evaluation contract; gates before judgement
- claude-md-optimizer — content tiers; verbatim moves; decline at target
- please-optimize-my-claude — dedupe; misplacement; per-directory load
- contextstellar — cache-friendliness as a dimension
- agentskills.io, skill-creator, Anthropic skill best practices — trigger evals with near-misses; a baseline every round
- karpathy/autoresearch — one editable surface; a results ledger; the simplicity rule
- google-research/harness2 (Harness², arXiv 2610.14224) — the per-domain experience library, four edit verdicts, one lesson with cue and evidence or none, the cheapest-component table, a 1-of-k failure as noise
- skill-receipts — the placebo comparison
- cloudflare web-perf, borghei performance-profiler — skip zero-impact work; evidence per fix
- LLM-judge research (self-preference, style bias, position bias) and Hamel Husain's judge guide
- Kalibera–Jones, pyperf, Tratt — benchmarking statistics
- Brendan Gregg (USE method, flame graphs); Amdahl's law; Theory of Constraints
- Kohavi — guardrail metrics; Google SRE — cost of each extra nine
- Chesterton's fence; Hyrum's law; AIP-180 — why removal needs a reason
- Diátaxis; plain-language guidance — docs tested on readers
- Lean / kaizen / DMAIC control plans — holding the gain
- local: `rev` (stop rule, isolated review), impeccable distill / clarify,
  code-simplifier (clarity over brevity), and impeccable's UI optimize skill
  (measure first, biggest bottleneck first) — the basis of `references/ui-performance.md`
