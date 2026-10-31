---
name: tune
author: shrix
description: "(shrix) The optimizer — makes anything that already exists faster, cheaper or clearer with its purpose unchanged (code, scripts, SQL, tests, docs, rules, skills, prompts, designs, Claude Code setup (hooks, MCP, settings, context load), configs, CI, data, assets); every gain measured against a stated goal. Triggers on /tune, 'optimize this', 'make X faster / smaller / leaner / clearer', 'cut the tokens', 'slim this down'. NOT a redesign, a bug hunt (/rev), doc–code sync (/spec), a cleanup of a fresh diff (/simplify) or a repo audit (/code-audit)."
metadata:
  version: "1.2"
  category: workflow
---

# tune — the optimizer: measurably better, against a stated goal

**Optimize, never redefine.** The artifact's purpose, behaviour and meaning
stay exactly as they are; only its form and its cost change — faster,
smaller, clearer, leaner. The result is a fully optimal version of the SAME
thing. Anything that would change what it does, says or offers is a redesign:
name it as a separate proposal, never apply it as part of the run.

Owns one capability: **goal-driven, measured optimization** of whatever it is
pointed at. It is not a bug hunt (`/rev`) and not doc–code sync
(`/spec`); when the ask is really theirs, say so and hand off. Security
findings are reported, never "optimized away".

## Stance — what every run embodies
- **Work on the constraint.** Measure before choosing where to work; the few
  biggest costs go first. Anything under ~5 % of the target's total cost for
  the goal metric is left alone.
- **One goal metric, plus guardrails that must not get worse.** A single
  score becomes a target and gets gamed.
- **Stop at what the user can perceive.** Past that, gains cost more than they return.
- **Same result with less wins; a tiny gain that adds complexity loses.**
- **Remove only what you know the reason for.** Every observable behaviour
  may be someone's contract.
- **Every number cites the command that produced it** — otherwise it is
  labelled unverified. Following the steps is not the same as the gain.

## Invocation
| form | meaning |
|---|---|
| `/tune` | infer target and goal from context |
| `/tune <target>` | a path, glob, skill name, `rules`, `settings`, `setup`, or `this` |
| `/tune <target> for <goal>` | `speed` · `size` · `clarity` · `tokens` · `cost` · free text |
| `--dry` | contract, baseline and one isolated diagnosis — no edits |
| `--rigorous` | force measured evidence: execute the artifact wherever its profile allows (`references/judging.md` § Rigorous) |

## 1. Resolve — ask only what cannot be inferred
1. **Target:** the argument → the artifact the conversation is working on →
   uncommitted changes in the current repo → ask, once.
2. **Profile:** from path and content (`references/profiles.md`). The most
   specific match sets the goal; the gates are the union of every match.
3. **Goal:** the argument, else the profile's default goal.
4. **Where it lives:** inside or outside the project tree (decides §5),
   git-tracked or not (decides the restore path).
5. **The repo's own commands:** discover its build, test, lint and benchmark
   commands from its manifests and docs — never invent them. Not in a repo →
   skip this, and say so.
6. **Quick check:** already below the point users notice, or too small for
   any gain to matter → decline now, before writing a contract.

## 2. Contract — written before any edit, printed first in the report
- **Goal metric** and its direction.
- **Guardrails:** every other dimension that matters here — "no worse than
  baseline" (`references/dimensions.md`).
- **Hard gates** from the profile. A gate the baseline already fails becomes
  part of the goal: it must not get worse, and reaching it is the threshold.
- **Evidence mode:** `run` (measured), `judge` (subjective goals only), or
  `run + samples` (prompts, skills, rules: measure, and guard behaviour with
  held-out samples). `--rigorous` forces `run` wherever the profile allows.
- **Acceptance threshold,** including the point users stop perceiving. With
  no established budget, propose one here and label it *proposed*.
- **Editable surface:** exactly what may change, including where moved
  content goes (rules → an on-demand `<topic>.md`, linked by a pointer that
  says when to read it). Tests, benchmarks, fixtures, eval samples and
  this contract are read-only for the whole run.
- **Start copy,** before the first edit:
  `scripts/snapshot.py snapshot .tune/<run> <every target path>`.

## 3. Baseline and constraint
- Measure the artifact as it is. Timings: warm up, repeat, median and spread
  (`references/judging.md` § Noise).
- Locate the constraint with the profile's tool — profiler, `--durations`,
  `EXPLAIN (ANALYZE, BUFFERS)`, `/context`, token counts, bundle analyzer.
  Rank findings by their share of the target's total.
- **Tool missing** → use the fallback in `references/judging.md` § Fallbacks
  and label the number an estimate. **The sandbox blocks the path to
  measure** → report it unmeasured, never extrapolate, and give the user the
  command that measures it.
- **Already at the threshold → decline, say why, stop.** A clean result is a result.
- `--dry` runs one isolated diagnosis (§4 step 1) on the ranked findings and stops.

## 4. Loop — at most 3 rounds, on a scratch copy
1. **Diagnose.** An isolated subagent reads the artifact, the evidence and
   the attempt ledger, and returns findings with the WHY, ranked by impact.
2. **Change.** One hypothesis per batch, on the top finding, so every effect
   stays attributable.
3. **Gates.** Hard gates and guardrails; any failure reverts the batch.
   A diff proves the read-only surface is untouched. A gate that runs tests
   runs the tests the batch affects — the changed files' own tests plus the
   tests of what imports them (`~/.agents/skills/_shared/references/test-runs.md`
   has the selection per runner) — the same set at the baseline; the full
   suite only when the user asks for it.
4. **Judge.** `references/judging.md`: measure objective goals; judge
   subjective ones pairwise, debiased. A candidate must beat the baseline AND
   a placebo rewrite. Prompts, skills and rules are diagnosed on one sample
   set and accepted on a held-out one.
5. **Ledger.** One line per attempt: id · change · metric · kept / reverted /
   crashed · why. It feeds the next diagnosis.
6. **Stop** when the threshold is met, a round gains nothing (after one
   structurally different attempt), round 3 ends, or two rounds pass with
   only the judge's opinion and no measured signal. A gain of 2× or more gets
   an adversarial re-check before it is accepted.

## 5. Apply
- **Double-check before applying:** re-read the exact diff and validate it
  with the real tool — a parser, `bash -n`, the tests, a dry run; a regex or
  eyeball check is not validation. Bulk or outside-the-project changes are
  staged in `.tune/<run>/after/` first and applied only once they pass —
  `scripts/snapshot.py check <staged paths>`.
- **Inside the project tree:** apply the best candidate.
- **Outside it** (`~/.claude`, `~/.agents`, other repos, the machine): show
  the diff, apply on yes. Anything not the user's own goes in a separate
  list, each item marked "not yours — an update will overwrite it" and given
  its own specific yes; a yes to the diff never covers them.
- A profile's proposals wait for their own yes.
- Deleting files or blocks the user wrote: ask first, wait for an explicit yes.
- Irreversible moves (history rewrites, lossy re-encodes): report only.
- **Restore path:** git, or a timestamped `before/` + `after/` copy in the
  current project's `.tune/<run>/` — never only in scratch, which is
  wiped when the session ends. The report prints the restore command.
- **Every decision stays revertible on its own,** after the report too: keep
  the pre-change copy of every file touched and a note of which decision
  changed which lines, so one decision can be undone without the others.
## 6. Hold the gain
Install the profile's guard as a ratchet — the new number becomes the floor:
a size budget, a CI benchmark, a lint cap, a line cap, a test. Inside the
project, add it; outside, propose it. No automatable guard → say so.

## 7. Report
Contract · baseline → final with % change, each number with its command ·
rounds and ledger summary · what changed and why · what was removed and why
· judge statistics (win / tie / loss, bias checks passed) · findings left
unfixed, named · guard installed · restore command.

The report is AUTHENTIC by construction: it is built from a mechanical diff
of the start copy (taken before the first edit) against the end state — never
from memory of what was done. A difference the run did not make (someone
else edited the file meanwhile) is flagged, not absorbed —
`scripts/snapshot.py diff .tune/<run> --md --expect <file listing the run's changed paths>`.

It ENDS with the **snapshot** — on EVERY run, one table row for EVERY change
made: `#` · the change · why (its rationale) · saving (metric before →
after, and %) · status. Nothing applied is left out of it. A run across
several areas ends with one cumulative snapshot plus a totals row; per-row
savings that are estimates are labelled so, and the totals row is measured.
Under it: how to revert — "revert `<#>`" undoes that one change; the
restore command undoes the whole run.

Then **Deleted** — every file, rule, block or line removed rather than
moved, with the approval it had and where the original is kept; or the line
"Nothing deleted." Nothing is ever deleted without the user knowing, and this
section is how they know.

## Never
- Change anything that isn't the user's own: plugins, caches, Claude Code's
  own data, third-party skills and packages get findings only, unless the
  user gives a specific yes for that item.
- Redefine the artifact: remove or alter a feature, fact, flow, API or
  capability. That is a redesign — a separate proposal, never part of the run.
- Change code behaviour, lose a fact, or drop a deny / ask rule or guard for tidiness.
- Edit tests, benchmarks, fixtures, eval samples or the contract mid-run.
- Move or print a secret; touch content that CI or scripts match on.
- Optimize coupled parts separately, or batch several hypotheses into one change.
- Population search, external API keys, hundreds of runs, readability grades
  as targets, or an automated accessibility pass treated as compliance.

## Proportionate
A trivial target gets one round, and the report says so. Scale the evidence
to the stakes — light checks for a small, reversible change, full evidence
for a risky or irreversible one: sample counts, runs and rounds shrink
with the size of the change (`references/judging.md` § Held-out samples).

## References
| file | holds |
|---|---|
| `references/profiles.md` | every profile: detection, default goal, gates, measure, safe moves, guard |
| `references/dimensions.md` | goal and guardrail dimensions: measure, tool, safe wins, perceptible threshold |
| `references/judging.md` | judge protocol, bias controls, placebo, held-out sets, timing noise, fallbacks |
| `references/ui-performance.md` | the UI speed checklist |
| `scripts/snapshot.py` | start copy · pre-apply check · diff-built report (`-h`) |
| `DESIGN.md` | why the skill is built this way, and its sources |
