---
name: code-audit
author: shrix
description: "(shrix) Use when asked for a comprehensive audit or health review of the whole repo/codebase — 'audit this repo', 'full audit', 'codebase health check', 'review the whole project', periodic quality sweep. Read-only: reports findings, never modifies anything. NOT for reviewing a diff, branch, or PR (use /code-review directly or the code-review plugin)."
---

# Code Audit — whole-repo audit

## Overview

A read-only audit of the entire repository: seven independent lenses run in parallel as
subagent sweeps, aggregated into one prioritized, categorized report. Each lens catches
what the others structurally cannot (a defect hunter cannot see undocumented behavior;
a docs-conformance pass is a shallow bug hunter; no static sweep observes runtime).

**Hard rules:**
- **Modifies nothing.** No edits, no commits, no fixes — not even "trivial" one-liners.
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

## Gates — run a lens only when its predicate holds

| # | Lens            | Mechanism                                | Run when                                        |
|---|-----------------|------------------------------------------|--------------------------------------------------|
| 1 | Design challenge| Adversarial pass on the ARCHITECTURE via the **`clodex`** skill — a multi-round Claude+Codex dialectic, so the second opinion comes from a DIFFERENT vendor's model. ⚠️ **STANDING AUTHORIZATION (owner, 14Aug26): `/code-audit` MAY invoke `clodex`** — the sole exception to clodex's user-invocation-only rule, and the only Codex path that reaches Codex from inside the sandbox. ⚠️ Never `codex:codex-rescue` (sandbox denies its plugin state dir; not editable in `settings.json`), never `codex:adversarial-review` / `codex:review` (both `disable-model-invocation: true`). ⚠️ **PREREQUISITE — verify, never assume:** run `codex doctor` FIRST and confirm `✓ auth`; anything else means the lens did NOT run and the report must say so rather than counting it. ⚠️ The prompt must carry the adversarial mandate: challenge whether this design is the right one, what assumptions it rests on, and where it fails under real conditions; review-only, never fixes. ⚠️ Spends real Codex tokens each run — gate it honestly rather than firing it every time | repo has non-trivial structure (2+ subsystems) AND the architecture is in question — a design/spec change landed, a redesign-class finding surfaced, or the user doubts the design. NOT for a routine re-audit of unchanged architecture (say so in Not checked) |
| 2 | Conformance     | isolated subagent(s): docs claims vs code reality, drift in BOTH directions | project claims exist (from intake) |
| 3 | Defect hunt     | parallel subagent sweeps, one per subsystem | ALWAYS. Cap at 10 sweeps, largest subsystems first — and report what was left out (no silent caps) |
| 4 | Security        | subagent sweep: secrets in code/config/history, injection, authn/authz, input handling, dependency risk | any security surface exists |
| 5 | Runtime verify  | exercise the core flows: build, test suite, main user paths — observe, change nothing | a runnable surface exists (skip for docs-only repos) |
| 6 | Coverage gaps   | subagent: map the critical paths and security surfaces against the test suite; name untested behaviors and missing regression tests (distinct from lens 5, which only runs what exists) | source code exists — with a test suite present, analyze it for gaps; with none, the lens reports that absence as its single Important finding |
| 7 | Performance     | subagent sweep: algorithmic hotspots, N+1 queries, unbounded growth, blocking I/O on hot paths. Scope split with lens 3: correctness/logic defects stay there; scale/perf characteristics belong here even when framed as bugs | a perf-sensitive surface exists (request-serving path, large-data processing, UI rendering) or the user flags slowness; when the repo serves a web UI, include a web-perf (Core Web Vitals) pass |

Gate honestly: a skipped lens MUST appear in the report with its reason. Never skip
silently; never run a lens its predicate doesn't justify.

## Execution — parallel, read-only

Launch ALL gated lenses (and their per-subsystem sweeps) concurrently against the
recorded state — independent and read-only, nothing to sequence. Wall-clock = the
slowest lens. Each sweep subagent gets: its lens mandate, its subsystem slice, the
project-claims pointers, and the two hard rules above.

## Aggregation

1. **Dedupe** — the same issue surfaced by multiple lenses or sweeps becomes ONE
   finding. Cross-lens agreement raises confidence; it must not inflate the count.
2. **Verify** — check each Critical/Important finding against the actual code before
   reporting it (reviewers can be wrong). Downgrade or drop what doesn't hold up.
   A Critical design finding (redesign-class) is arbitrated with a targeted `clodex`
   dialectic on that specific question before the report asserts it.
3. **Categorize + prioritize** — group findings under categories named in the
   project's own vocabulary: its subsystems, workers, workflows, and concerns, as
   the findings cluster them (e.g. "Auth & sessions", "Capture/ingest — data
   integrity", "Deploy & release process", "Resilience & platform limits",
   "Architecture / structural (longer-horizon)", "Documentation drift"). Invent the
   categories per audit — there is no fixed taxonomy, and lens/tool names are never
   categories. Mixing subsystem, concern, and horizon categories is fine when that
   clusters the findings best. Order categories by their most severe finding; within
   a category, Critical → Important → Nit.

## Report (required shape — all four slots, in order)

1. **Verdict line:** healthy / needs-attention / at-risk — plus the audited state
   (HEAD SHA, dirty or clean).
2. **Findings by category** — the deduped findings under the categories from
   aggregation, each entry `[Critical|Important|Nit] file:line — issue` — the
   bracketed severity is the line's ONE priority marker; no separate rank numbers.
   In the report entry, each finding also carries a 2–3 line description (about two
   sentences) folded into its bullet — enough to understand what breaks and why it
   matters; no essays. No tool or lens names anywhere in the findings: the reader cares
   about the problem, not the plumbing.
3. **Not checked** — every skipped lens and every capped sweep in plain language with
   its reason (e.g. "runtime flows not exercised — no runnable surface"). REQUIRED
   even when empty ("Not checked: nothing — all applicable checks ran").
4. **Suggested next steps** — a short ordered fix list, most urgent first, naming
   the specific findings to start with; offers only. The audit itself changes
   nothing; then WAIT for the user.

**Deliverable:** prepend the audit as ONE entry to `docs/logs/revlogs.md` in the
audited project. If missing, create `docs/logs/` and the file with a
`# <ProjectName> Review Logs` header (project name from git remote basename or
directory) plus a dashed underline. Entries are newest-first, inserted directly
after the header, one blank line between entries, NO `---` separators. Entry shape:
- `[DDMonYY/H.MMx]` timestamp line (x = `a`/`p`, e.g. `[12Jul26/3.05p]`) — the run
  time, a single timestamp, never a range; no individual timestamps on bullets
- `> **verdict — scope**` bold summary line: healthy/needs-attention/at-risk, the
  short HEAD SHA, clean/dirty state, and lens count (e.g. `6/7 lenses`). Lowercase
  prose, but acronyms and proper nouns keep their conventional capitalization
- `- ` bullets (markdown `- ` markers, never `• `): the findings grouped by
  category — bold the category name ONCE, on the first finding bullet of each
  category; subsequent same-category bullets stay plain. Each finding is
  `[Critical|Important|Nit] file:line — issue`, with its 2–3 line description
  joined onto the SAME physical line after a `; ` (never a literal line break
  inside a bullet — a continuation line can break out of the list when rendered).
  Then one `- **Not checked:**` bullet (required, even if "nothing"); then one
  `- **Next steps:**` bullet, most urgent first.

This file is the audit's ONLY write. Committing it is the user's call. Secret
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
