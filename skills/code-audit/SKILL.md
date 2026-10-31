---
name: code-audit
author: shrix
description: "(shrix) Audit or health review of the whole repo — 'audit this repo', 'full audit', 'codebase health check', 'review the whole project', periodic quality sweep. Read-only: reports verified findings and the trend since the previous audit; writes only its revlogs entry. NOT for a diff, branch or PR (use /code-review)."
---

# Code Audit — whole-repo audit

## Overview

A read-only audit of the entire repository: seven independent lenses run in parallel as
subagent sweeps, aggregated into one prioritized, categorized report. Each lens catches
what the others structurally cannot (a defect hunter cannot see undocumented behavior;
a docs-conformance pass is a shallow bug hunter; no static sweep observes runtime).

**Hard rules:**
- **Modifies nothing.** No edits, no fixes — not even "trivial" one-liners.
  Findings are reported; fixing is a separate, user-initiated step. Sole exception:
  prepending the `revlogs.md` entry itself (see Report below).
- **All reads are fully permitted.** Lenses read anything in the repo — code, configs,
  docs, scripts, git history — without asking. Never paste a discovered secret's VALUE
  into any report or finding; report its location only.

## Stage 0 — Intake (always)

1. **State.** Record HEAD SHA + dirty files; the repo is audited as-is. No repo edits
   by anyone while the audit runs, so findings stay anchored.
2. **Inventory.** Map the subsystems: top-level dirs, services, workers, entry points,
   CI/deploy configs, docs. This map drives sweep fan-out, gates, and categories.
3. **Project claims.** Locate what the project says about itself — README, docs/,
   specs, CLAUDE.md, manifests. This is the conformance baseline.
4. **Surfaces.** Note security surfaces (auth, network I/O, user input, DB, secrets)
   and runnable surfaces (build, test suite, main flows) for the gates.
5. **Previous audit.** Read the newest whole-repo audit entry in
   `docs/logs/revlogs.md` (its summary line counts lenses, e.g. `6/7 lenses`;
   skip fix-only entries) and take its short SHA, in whatever form it appears
   (`` `abc1234` ``, `HEAD abc1234`, `@ abc1234`). Gone from history
   (`git cat-file -e <sha>^{commit}` fails, e.g. after a rebase) or no entry → no
   baseline: say so and audit without one. With a baseline:
   - `git diff --stat <sha>..HEAD` weights the sweeps toward what changed — it
     never narrows them: the scope stays the whole repo.
   - Lens 1's "architecture in question" holds when arch, spec or design docs
     changed or a top-level directory was added or removed since `<sha>`.
   - Every Critical and Important of that entry is carried forward and
     re-checked in the verify wave: fixed · still open · regressed. Match by
     file + symbol + issue, never by line number; say when a match is uncertain.
6. **Risk order.** Churn per file over 12 months
   (`git log --since=12.months --numstat --format=`, added + deleted) times its
   size orders the defect sweeps, and the top hotspot files are named in their
   sweep's brief for a deeper read. No history → largest subsystems first.
7. **Check log** (`~/.agents/skills/_shared/references/checks.md`). Read only:
   `bash ~/.agents/skills/_shared/scripts/checks.sh has tests` exit 0 → lens 5
   runs the build and main flows but not the suite again; `has docs` exit 0 →
   lens 2 is skipped as passed. Say so in Not checked. Never `pass`: the audit
   records nothing (`has` adds blobs to git's object store; no tracked or
   working-tree file changes).

## Gates — run a lens only when its predicate holds

| # | Lens            | Mechanism                                | Run when                                        |
|---|-----------------|------------------------------------------|--------------------------------------------------|
| 1 | Design challenge| Adversarial pass on the ARCHITECTURE via the **`clodex`** skill — a multi-round Claude+Codex dialectic, so the second opinion comes from a DIFFERENT vendor's model. ⚠️ **STANDING AUTHORIZATION (owner, 14Aug26): `/code-audit` MAY invoke `clodex`** — the sole exception to clodex's user-invocation-only rule, and the only Codex path that reaches Codex from inside the sandbox. ⚠️ Never `codex:codex-rescue` (sandbox denies its plugin state dir; not editable in `settings.json`), never `codex:adversarial-review` / `codex:review` (both `disable-model-invocation: true`). ⚠️ **PREREQUISITE — verify, never assume:** clodex's Step 0.1 readiness check (`_shared/scripts/codex-preflight.sh`, which runs `codex setup --json`) must pass; anything else means the lens did NOT run and the report must say so rather than counting it. ⚠️ The prompt must carry the adversarial mandate: challenge whether this design is the right one, what assumptions it rests on, and where it fails under real conditions; review-only, never fixes. ⚠️ Spends real Codex tokens each run — gate it honestly rather than firing it every time | repo has non-trivial structure (2+ subsystems) AND the architecture is in question — a design/spec change landed — since the previous audit (Stage 0 step 5), or recently by `git log` when there is no baseline — a redesign-class finding surfaced, or the user doubts the design. NOT for a routine re-audit of unchanged architecture (say so in Not checked) |
| 2 | Conformance     | isolated subagent(s) that follow **`spec`'s Verify** (`~/.agents/skills/spec/references/docs.md` § Verify) over the whole project: docs claims vs code reality, drift in BOTH directions — spec owns this check, the lens only runs it read-only: checklist items that need EXECUTION ("Installation steps work", "Quick start example runs", examples tested) are judged by reading, never run, and reported as unexecuted; and it records nothing in the check log — this audit's only write is its revlog entry | project claims exist (from intake), and no `docs` pass in the check log (Stage 0 step 7) |
| 3 | Defect hunt     | parallel subagent sweeps, one per subsystem | ALWAYS. Cap at 10 sweeps, in Stage 0's risk order — and report what was left out (no silent caps) |
| 4 | Security        | subagent runs secscan read-only: `python3 ~/.agents/skills/secscan/scripts/scan.py full --json` (a Terminal-panel tab when one exists; engines it reports `blocked` go under Not checked with its command), then verifies the engine results per `~/.agents/skills/secscan/references/verify.md` (its panel may run nested, else self-verified and labelled) — no `--report`, no fixes. The code review itself is `claude-security`'s, which cannot run inside a subagent: the audit's Next steps name `/claude-security` "Scan codebase" (after a clean secrets run) and, for depth, the `security-audit` skill. The brief carries secscan's secret rules: the subagent builds the masked mirror (`scan.py mirror $TMPDIR/secscan-mirror-<sha12>`) and reads only that, never the repo, deleting it when done; a secret-named file is never read; a history hit's commit and file are never shown; never quote a value. Findings fold into this audit's categories | any security surface exists |
| 5 | Runtime verify  | exercise the core flows: build, test suite, main user paths — observe, change nothing. Runs `~/.agents/skills/_shared/references/test-runs.md`'s rule: a failing test is re-run once alone, and a flaky one is named, not reported as a defect. The suite is skipped on a `tests` pass (Stage 0 step 7) | a runnable surface exists (skip for docs-only repos) |
| 6 | Coverage gaps   | subagent that follows **`test`'s Analyze mode** (`~/.agents/skills/test/SKILL.md` § Analyze Mode): map the critical paths and security surfaces against the test suite; name untested behaviors and missing regression tests (distinct from lens 5, which only runs what exists) — `test` owns the analysis, the lens runs it read-only and generates nothing — no coverage run or any other step that writes files (coverage reports, caches); analysis by reading only | source code exists — with a test suite present, analyze it for gaps; with none, the lens reports that absence as its single Important finding |
| 7 | Performance     | subagent sweep: algorithmic hotspots, N+1 queries, unbounded growth, blocking I/O on hot paths. Scope split with lens 3: correctness/logic defects stay there; scale/perf characteristics belong here even when framed as bugs | a perf-sensitive surface exists (request-serving path, large-data processing, UI rendering) or the user flags slowness; when the repo serves a web UI, include a web-perf (Core Web Vitals) pass |

Gate honestly: a skipped lens MUST appear in the report with its reason. Never skip
silently; never run a lens its predicate doesn't justify.

## Execution — parallel, read-only

Launch ALL gated lenses (and their per-subsystem sweeps) concurrently against the
recorded state — independent and read-only, nothing to sequence. Wall-clock = the
slowest lens. Each sweep subagent gets: its lens mandate, its subsystem slice (with
its hotspot files from Stage 0), the project-claims pointers, and the two hard rules
above.

## Aggregation

1. **Dedupe** — the same issue surfaced by multiple lenses or sweeps becomes ONE
   finding. Cross-lens agreement raises confidence; it must not inflate the count.
2. **Verify — isolated, trying to refute** (reviewers can be wrong). One isolated
   verifier subagent per category, told to REFUTE each Critical and Important and
   to re-check the previous audit's carried-forward findings. A finding survives
   only with a `file:line` plus a trigger (input → wrong outcome) or a static
   trace; otherwise downgrade or drop it. Each survivor gets one check tag:
   `proven` (executed, with a control showing the check could fail) · `traced`
   (the path followed end to end in the code) · `unverified` (neither; never
   reported as Critical). Repros run only in a scratch copy or `$TMPDIR`, never
   in the repo. A Critical design finding (redesign-class) is arbitrated with a
   targeted `clodex` dialectic on that specific question before the report
   asserts it.
3. **Categorize + prioritize** — group findings under categories named in the
   project's own vocabulary: its subsystems, workers, workflows, and concerns, as
   the findings cluster them (e.g. "Auth & sessions", "Capture/ingest — data
   integrity", "Deploy & release process", "Resilience & platform limits",
   "Architecture / structural (longer-horizon)", "Documentation drift"). Invent the
   categories per audit — there is no fixed taxonomy, and lens/tool names are never
   categories. Mixing subsystem, concern, and horizon categories is fine when that
   clusters the findings best. Order categories by their most severe finding; within
   a category, Critical → Important → Minor.

**Severity is impact, never confidence** (confidence is the check tag). Only these
three labels — the same scale `/rev` and `/dev` use (older revlogs say `Nit`; read
it as Minor):
- **Critical** — breaks or leaks under normal use now: data loss or corruption, a
  security exposure, a core flow down, a ship blocker.
- **Important** — a real defect or risk that bites under a plausible condition,
  or blocks change; fix soon.
- **Minor** — quality, clarity or consistency, with no behaviour at risk. At most 5
  per category in the report; the rest as a count (`+7 more Minor`).

## Report (required shape — all four slots, in order)

1. **Verdict line:** healthy / needs-attention / at-risk — plus the audited state
   (HEAD SHA, dirty or clean) and, with a baseline, the trend against it:
   `Crit 6→2 · Imp 25→9 · 4 new · 3 fixed`.
2. **Findings by category** — the deduped findings under the categories from
   aggregation, each entry `[Critical|Important|Minor] A<n> file:line — issue (<check tag>)`
   — the bracketed severity is the line's ONE priority marker. `A<n>` is a handle
   for Next steps and the next audit, numbered in report order; it is not a rank.
   A carried-forward finding adds `open since <date>` or `regressed`.
   In the report entry, each finding also carries a 2–3 line description (about two
   sentences) folded into its bullet — enough to understand what breaks and why it
   matters; no essays. No tool or lens names anywhere in the findings: the reader cares
   about the problem, not the plumbing.
3. **Not checked** — every skipped lens and every capped sweep in plain language with
   its reason (e.g. "runtime flows not exercised — no runnable surface"), each
   ending in the exact command that would run it (a ready `/clodex <mandate>`,
   `npm audit`, the suite's command). REQUIRED even when empty ("Not checked:
   nothing — all applicable checks ran").
4. **Suggested next steps** — a short ordered list, most urgent first, each naming
   its finding IDs and the skill that owns the fix: `/rev A1 A4` for defects,
   `/spec update` for doc drift, `/test` for missing tests, `/spec` for a
   redesign-class finding, `/tune` for measured performance. Decisions only the
   owner can make are listed apart. Offers only. The audit itself changes
   nothing; then WAIT for the user.

**Deliverable:** prepend the audit as ONE entry to `docs/logs/revlogs.md` in the
audited project. If missing, create `docs/logs/` and the file with a
`# <ProjectName> Review Logs` header (project name from git remote basename or
directory) plus a dashed underline. Entries are newest-first, inserted directly
after the header, one blank line between entries, NO `---` separators. Entry shape:
- `[DDMonYY/H.MMx]` timestamp line (x = `a`/`p`, e.g. `[12Jul26/3.05p]`) — the run
  time, a single timestamp, never a range; no individual timestamps on bullets
- `> **verdict — scope**` bold summary line: healthy/needs-attention/at-risk, the
  short HEAD SHA, clean/dirty state, lens count (e.g. `6/7 lenses`) and the trend
  when there is a baseline. Lowercase
  prose, but acronyms and proper nouns keep their conventional capitalization
- `- ` bullets (markdown `- ` markers, never `• `): the findings grouped by
  category — bold the category name ONCE, on the first finding bullet of each
  category; subsequent same-category bullets stay plain. Each finding uses the
  Report item 2 format, with its description joined onto the SAME physical line
  after a `; ` (never a literal line break inside a bullet — a continuation line
  can break out of the list when rendered). Then one `- **Not checked:**` bullet
  (Report item 3); then one `- **Next steps:**` bullet, most urgent first.

This file is the audit's ONLY write to the repo (repros live in scratch or `$TMPDIR`;
`checks.sh has` adds only git objects). Committing it is the user's call. Secret
handling: report locations, never values. In
chat, reply with a SUMMARY: the verdict, then ALL findings category-wise as
one-liners (`[severity] issue` — no detailed descriptions), and the file path. The
detailed descriptions live only in the file.

## Common mistakes

| Mistake                                            | Reality                                                                       |
|----------------------------------------------------|--------------------------------------------------------------------------------|
| Reporting per-tool or per-sweep reports            | The deliverable is ONE categorized, prioritized report. Aggregation is the job.|
| Naming the tool/lens next to a finding             | Findings are grouped by problem category; the plumbing stays invisible.       |
| Counting the same issue once per lens that found it| Dedupe first; overlap is confidence, not volume.                              |
| Auditing only src/ and skipping the rest           | The repo is the scope — CI, deploy configs, scripts, and docs are surfaces too.|
| Committing or pushing `revlogs.md`                 | Prepending its entry is the audit's only write; git stays with the user.      |
