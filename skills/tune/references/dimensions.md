# Dimensions

A contract names ONE goal dimension and treats the others that matter as
guardrails: "no worse than the baseline". Use this table to pick both, the
tool that measures them, and where improvement stops being worth it.

| dimension | measure | tool | safe wins | stop at |
|---|---|---|---|---|
| latency | p50 / p95 / p99 — tails, not means | profiler, flame graph, Lighthouse CI | cache; parallelise independent calls; fewer round trips | 0.1 s feels instant · 1 s keeps flow · 10 s loses attention |
| throughput | operations/s at a fixed error rate | load generator, `hyperfine` | batch; remove serial sections | the demand actually seen |
| memory | peak RSS, heap | heap snapshot | stream instead of loading whole; drop caches that never hit | no swapping, headroom kept |
| size | bytes after brotli | `size-limit`, bundle analyzer | drop dependencies; modern image formats; font subsets | the budget |
| tokens / context | tokens loaded per turn; cache-hit % | `/context`, API `usage` | stable content first; move reference detail out of always-loaded files | the budget per turn, or one proposed in the contract |
| LLM cost / latency | $ per task; time to first token; output tokens | API `usage` fields | cached prefix; batch; route easy work to a smaller model; shorter output; no LLM where plain code does | the budget per task |
| cloud cost | $ per unit of work | FinOps reports | delete idle; rightsize; schedule; commit for steady load | unit cost target |
| energy | SCI = (E·I + M) / R | GSF SCI | move fewer bytes; scale down when idle | — |
| accessibility | WCAG 2.2 AA failures | `axe-core` (~57 % of issues) + a manual pass | labels, alt text, contrast, target size | zero AA failures |
| web vitals / SEO | LCP, INP, CLS at p75 | Lighthouse, CrUX | right-size the LCP image; reserve space | LCP ≤ 2.5 s · INP ≤ 200 ms · CLS ≤ 0.1 |
| security posture | per-check score | OpenSSF Scorecard | pin actions; least-privilege tokens; branch protection | never traded for another dimension |
| maintainability | cognitive complexity; churn × complexity hotspots | git log, a complexity linter | refactor only the top hotspots | complexity ≤ 15 per function |
| clarity (text) | a fresh reader answers task questions | isolated subagent | say it once; current state first; one term per concept | answers are right and fast |
| reliability | flaky rate; error-budget burn | rerun statistics | quarantine flaky tests; shrink large tests | the SLO — each extra nine can cost ~100× more |
| onboarding | time to first useful change | stopwatch | one-command setup | — |
| toil / process | human minutes per run; waiting share | value-stream mapping | cut handoffs and waits | time saved > cost to build and maintain |

## Picking guardrails
- Speed goals guard correctness, memory and accessibility.
- Size and token goals guard behaviour and clarity — nothing lost.
- Clarity goals guard facts and coverage.
- Cost goals guard latency and quality.
- Security posture is never a trade-off; a finding is reported, not optimized away.
