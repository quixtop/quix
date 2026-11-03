# Judging and measurement

How `/tune` decides a candidate is better. Measurement beats opinion:
judge only what cannot be measured.

## Objective goals — measure
Speed, size, tokens, cost, counts: measure baseline and candidate the same
way, on the same machine, and cite the command for every number.

## Rigorous
`--rigorous` forces measured evidence wherever the profile allows — execute
the artifact instead of judging its text:
| profile | instead of | run |
|---|---|---|
| prompt, skill, rules | reading the text | the held-out samples, each 3 times |
| docs | reading the text | a fresh subagent answering task questions from the doc |
| ui visual | screenshot judging | the real user flows, plus `axe` |
| code, shell, sql, hooks | static reasoning | the tests the batch affects, fixtures and benchmarks |
Profiles whose goal is purely subjective (tone, visual taste) keep the judge
and say so in the contract.

## Noise — timings
- Warm up first; then at least 5 runs, baseline and candidate interleaved (A B A B …).
- Report median and spread (IQR). Never the minimum — it misleads.
- Accept a change only when the difference exceeds the baseline's own
  run-to-run spread and its interval excludes zero.
- Small setup details skew timings (environment size, link order): keep them fixed.
- Label lab numbers and field numbers separately.

## Fallbacks — when the named tool is missing
Use the fallback and label the number an **estimate**:
| missing | fallback |
|---|---|
| `/context`, a tokenizer | characters ÷ 4 |
| `hyperfine` | a timing loop (`python3` `perf_counter`) with warm-up runs and the median |
| a profiler | timing each stage separately (`bash -x`, per-command timing) |
| the repo's commands (not a repo) | the profile's own gates only — say so |
A sandbox-blocked path is reported unmeasured (SKILL.md §3).

## Subjective goals — a debiased pairwise judge
The author and the judge are both Claude, and models favour their own
writing. So:
1. **Isolated.** The judge is a fresh subagent that sees the two versions,
   the contract and the criteria — never the author's reasoning.
2. **Blind, both orders.** Judge A-vs-B and B-vs-A. If the verdicts disagree,
   it is a tie.
3. **Normalised.** Strip formatting differences (markdown styling, spacing)
   before judging — style bias is the largest measured bias.
4. **Criteria, pass/fail.** One verdict per criterion, the critique written
   before the verdict.
5. **Different model family when one is available** in this environment;
   otherwise prefer measurement over opinion wherever possible.

## Placebo
Before judging, write a generic rewrite ("clearer, cleaner, leaner") that
does NOT use the diagnosed findings. A candidate must beat both the baseline
and the placebo. A generic rewrite can shift results through suggestion
alone; beating it proves the findings did the work.

## The judge is on trial
- Plant one known-worse candidate per run. If the judge does not reject it,
  its verdicts are void — say so and fall back to measurement.
- Flat verdicts (it cannot tell candidates apart) or flip-flopping ones
  (noise) are reported, never trusted.
- Opinion-only rounds are capped (SKILL.md §4 step 6): without an outside
  signal, self-correction often makes things worse.

## Held-out samples — prompts, skills, rules
- **Scale to the change:** ~6–10 behaviour probes for one rule file or
  prompt; ~20 realistic queries for a skill description, near-misses
  included. Run each sample 3 times — results vary.
- Split 60 / 40 and keep the split fixed. Diagnose from the training samples
  only; accept by the held-out score; pick the best version by held-out
  score, not the latest.
- A failure in one sample, or in one of a sample's 3 runs, is noise: a
  change aimed at it alone overfits. Aim at failures that repeat.
- No progress for a round? Suspect the samples before the artifact.

## Anti-gaming
- The read-only surface (SKILL.md §2) and the 2× re-check (§4 step 6)
  apply; the re-check tries to show the gain is a measurement artifact.
- Watch for a metric that improved while the goal did not.

## Report
Win / tie / loss counts, the effect size with its interval, which bias checks
ran, and whether the planted candidate was rejected.
