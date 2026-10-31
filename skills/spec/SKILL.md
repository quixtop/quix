---
name: spec
author: shrix
description: "(shrix) Every project doc in one skill. Before the build: turn a feature — given, or taken from the conversation — into a reviewed spec, plan, reqs, arch (with its diagrams), design and tasks, filed on ONE go, then offer /dev; in full mode it first drills the idea and attacks it with a panel of agents, and a panel reviews the spec. After the build: the same set plus README and API docs, written from the code. Keeps docs in sync: /spec update | verify | changelog; /spec review <file> reviews any doc. Use to spec a feature, think an idea through (/spec think), document existing code, update docs after changes, check docs against the code, review a doc, or write release notes — not quick ideation (superpowers:brainstorming) or the build itself (/dev)."
metadata:
  version: "0.5.0"
  category: documentation
---

# spec — every project doc

Writes every doc a project keeps — spec, plan, reqs, arch with its diagrams,
design, tasks, ADRs, README, API docs — reviews them as one set, fixes what
the review finds, and files them on ONE go from the user. **Before the
build** the docs come from the request and the discussion, and `/spec` stops
at offering `/dev`; **after the build** they come from the code. It also keeps
docs in sync with later changes (`update`, `verify`, `changelog`).

**Not for**: building (`/dev`), bug fixes or refactoring (`/rev`),
quick ideation (`superpowers:brainstorming`).

**Who writes what** — `/spec` writes every doc itself, except two: the plan,
written by `superpowers:writing-plans` (by `/spec` only when it is missing),
and the generated diagrams, by `/arch`.

**Safety gates** — `/spec` never pushes and never deletes a file. In the
feature flow (Steps 0–8) it writes nothing beyond the spec (the concept
at Step 3's save point included), its companions and the plan before the
user's go (Step 6); `update` and `changelog` write
directly, since the caller asked for exactly that, and `verify` writes no doc. Decisions made during the run go into the spec's To file
section, not the capture docs, until then. External skills are only invoked,
never edited.

Sections run in the order they are used.

---

## Invocation

```
/spec add ability to share chats with teammates
/spec light add a copy-link button   ← light mode, for a small feature
/spec                 ← takes the feature from the conversation
/spec think [idea]    ← full mode, Steps 1–3 only: stops at the save point (`draft — concept`)
/spec review <file>…  ← the review panel on existing docs; reports, changes nothing
/spec docs [path]     ← post-build: document code that already exists (a path narrows it)
/spec update [scope]  ← sync docs with code changes (a base SHA or BASE..HEAD; none → everything unpushed)
/spec verify [scope]  ← check docs against the code; report drift, fix nothing
/spec changelog       ← release notes since the last tag
/spec help            ← help, -h or --help as the sole argument: print this skill's description and these lines, then stop
```

- **`update`, `verify`, `changelog`** — READ `references/docs.md` and run
  that section only; Steps 0–8 do not run.
- **A mode word is a mode only** when it stands alone or is followed by what
  it takes — `update`/`verify`: a SHA or `BASE..HEAD`; `docs`, `review`: an
  existing path; `think`: the idea. Otherwise the whole text is a feature
  (`/spec update the login copy`). `think` alone takes the feature from the
  conversation, as bare `/spec`; it runs full mode only — `light think` is
  refused in one line. `review` alone asks which file; with one → READ
  `references/review.md` § Standalone review: Step 0.1 resolves `<root>` and
  0.2's plan lookup finds the plan; no other step runs.

- **With text** — that is the feature.
- **Bare** — take the feature from the conversation: the topic of the current
  chapter mark when it is feature-shaped (something to build, not an
  investigation), else the latest feature-shaped request. Announce it in one
  line — `Speccing: <feature>` — and go on. No candidate, or two that fit
  equally, → ask which feature.
- **Light** — `light` first, or offered on the drill's first turn when the
  feature is small, and taken only on the user's yes: one area of the code,
  about five plan tasks at most, nothing touching auth, secrets, user data
  or data that leaves the machine. User data = accounts, personal data about
  people, or content other people can see or send — not the project's own
  state, config, logs or check records, nor the owner's own local files;
  leaving the machine = sent over the network or to a third-party service (a
  push of the project's own repo excepted). Every step still runs, lighter:
  Steps 1–3 keep the one batch and the automatic pick; Step 4 writes only
  the spec sections that apply (no N/A filler), each companion it triggers
  always inside the spec — data and migration with rollback, the API
  contract, spike notes; Step 5 runs ONE reviewer (round 2 only after a Critical stored-data or interface fix). The go, the filing
  and the safety gates are unchanged. Only the threat model's trigger
  appearing mid-run switches Steps 4 onward to full (companions, the review panel), said in one
  line with the added cost — `switch to full: review panel 6 agents ·
  ~330k–450k tokens in place of one reviewer (~65k)`; the think stage is not
  replayed.

## Quick Reference

| step | does | output |
|---|---|---|
| 0. Resolve | project root, re-run check, `<feature>` name, tools, sources | — |
| 1. Vision | core intent, knowns and unknowns | chat (full: at the concept gate) |
| 2. Requirements | full: drill, concept gate (`think.md`) · light: CRITICAL questions in one batch, the rest assumed | chat, recorded in the spec (full: at the save point · light: at Step 4) |
| 3. Design | full: idea panel (triggered lenses), you pick on a scope or security difference, save point · light: the recommended approach taken | full: `draft — concept` spec · light: chat |
| 4. Generate | spec (with To file), companions, plan | `docs/spec/…`, `docs/plan/…` |
| 5. Review loop | full: a panel of 5 roles · else one isolated reviewer; fix or refute; re-review of the changed sections only after a Critical, scope or security fix (light mode: only a Critical stored-data or interface fix) | Review section in the spec |
| 6. Go / no-go | ONE approval for everything still to file | the user's answer |
| 7. File | capture docs and ADRs, Status, figures | the project's doc families |
| 8. Close | Final Package, opening with the key points; offer `/dev` | chat |

## Post-build mode

When the feature's code already exists (`/spec docs`, or Step 0.2 finds it),
the docs are written from the code, as built. The steps change only here:

- **Steps 1–3** — no vision or design options: the design is what was built.
  Step 2's batch asks only what the code cannot answer (which parts to
  document, who reads the docs); nothing to ask → no batch. Significant
  decisions found in the code get ADRs with `Status: Accepted`.
- **Step 4** — first, one isolated read-only reader per module, all in ONE
  wave, each returning what its module does, its interfaces, data and error
  paths, with file:line. The spec is written from those reports, every
  section as built; companions as triggered (an API contract from the code).
  **No plan** — nothing is left to build; To file has no `Build` task, and
  section 4.11 (Roadmap) reads `N/A — built`. To file also lists the README
  and API-doc entries, and the source files that get missing docstrings.
- **Step 5** — the reviewer checks every claim against the code instead of
  plan traceability and plan form.
- **Steps 6–7** — no plan to re-invoke, set or approve; everything is filed
  as built (no `(planned)` marks).
- **Step 8** — no `/dev` offer; the close says `documented` (close.md).

Code that is only partly built is not post-build: it runs the normal flow,
with each To file entry tagged `as-built` or `not built yet` by checking the
code. The plan covers only the `not built yet` entries, and the reviewer is
told that `as-built` requirements need no plan task.

---

## Step 0: Resolve

1. **Project root** (`<root>`) — the git root of the repo that holds the
   feature's code (`git rev-parse --show-toplevel`). Not a git repo → the
   current directory. When the feature's code is outside the current repo (a
   global script, another repo), ask for the root, and get the user's yes in
   chat to write there; no yes → stop here. Every path below is `<root>/…`,
   passed to other skills as an absolute path.
2. **Re-run check** — look through `<root>/docs/spec/` for this feature's
   spec, by its title and Feature Overview.
   - `/spec think` and an exact match → write nothing and say, in one line,
     "concept saved; run /spec <feature>" for a `draft — concept`, else
     "re-run /spec <feature> instead". Stop.
   - `/spec think` and the feature's code already built → "already built —
     /spec docs". Stop.
   - A `draft — concept` exact match → print `Resuming concept:
     docs/spec/<name>.md`, READ `references/think.md` § Save point and resume
     and § Contradictions; after Steps 0.4–0.5, start at Step 4.
   - An exact match → a re-run of that spec: announce it
     (`Re-run of docs/spec/<name>.md`); every output below is updated in
     place, never written a second time beside the old.
   - A loose match, or more than one → ask which spec, or whether this is a
     new feature.
   - Find the re-run's plan at `docs/plan/<feature>.md`, else as the plan
     under `docs/plan/` whose `Spec:` header line names this spec. A plan
     that exists and is not `Status: draft — awaiting go` (including one
     with no Status line at all) counts as approved → ask whether its build
     has started. Started → offer: **spec only**, or a follow-up feature
     under a new name. Never regenerate a plan in progress.
   - **Spec only** is for changes that need no build work — wording,
     clarifications, decisions already built, and dropping a planned
     decision; anything that needs build work goes to the follow-up feature.
     Steps 1–3 run as in light mode (no think stage); it changes Steps 4–8:
     READ `references/rerun.md` before Step 4.
   - **Built already?** `/spec docs`, or the feature's code exists with no
     spec → post-build mode (§ Post-build mode), said in one line. An
     existing spec is then updated in place from the code — no build-started
     question, no spec-only mode. `/spec docs` with no path documents the
     whole project; `<feature>` is the repo folder's name.
3. **`<feature>`** — for a new feature, a short kebab-case name
   (`chat-sharing`) such that none of `docs/spec/<feature>.md`, its companion
   names (`<feature>-api.md`, `-migration.md`, `-security.md`, `-spikes.md`)
   or `docs/plan/<feature>.md` is already used by another feature. A
   `draft — concept` holding the name you want → ask: resume it, or a new name.
4. **Tools** — check which hand-off skills are installed and say up front
   what is missing. Each has a fallback: without writing-plans, Step 4 writes
   the plan; without `/arch`, the figures are reported as
   `figure: stale — /arch not installed`.
5. **Sources**, read as the steps reach them — each step's independent reads
   and searches go out together in one wave:
   - Steps 1–2: existing features (the reqs family: `docs/reqs.md`,
     `docs/reqs/**`, `REQUIREMENTS.md`, `docs/requirements/**`, `reqs-*.md`) and
     work already owed (the tasks family: `tasks.md`, `docs/tasks/**`, `TODO.md`).
   - Step 3: architecture (the arch family: `arch.md`, `docs/arch.md`,
     `docs/arch/**`, `ARCHITECTURE.md`, per-module arch docs), past decisions
     (`docs/adr/` where kept) and experience conventions (the design family:
     `DESIGN.md`, `docs/design/**`).
   - Steps 3–4: the codebase — similar features, utilities, established
     patterns — and the project's rules file for code standards.

## Step 1: Vision

Full mode: READ `references/think.md` — it runs Steps 1–3. Light mode,
post-build mode and spec-only re-runs: READ `references/questions.md` — the
vision block (post-build: § Post-build mode) and Step 2's batch.

## Step 2: Requirements

Full mode: the drill and concept gate of `references/think.md`. Light mode and
spec-only re-runs: the batch of `references/questions.md` § Step 2 — the
run's one up-front ask; post-build mode: § Post-build mode, in that form.

## Step 3: Design

Brainstorm 2–4 approaches (light mode: 1–2) — for each: how it works, the
user flow, pros, cons, complexity, effort — compared in one table. Full mode:
first `references/think.md` § Idea panel, then § Approach pick and § Save
point and resume. Light mode: take the recommended one as an **Assumption**;
when the approaches differ on scope or security, the pick is a CRITICAL
decision and becomes an **Open question** instead. Draft an ADR (`Status:
Proposed`) for every significant decision, per
[references/adr-template.md](references/adr-template.md).

## Step 4: Generate

Write the set. Each file carries `Status: draft — awaiting go` under its
title until Step 7; no approval is needed yet.

1. **Spec** — `<root>/docs/spec/<feature>.md`: the 13 sections of
   [references/specification-template.md](references/specification-template.md),
   each filled or marked `N/A — <why>` (for a feature with no UI, swap the
   user-facing sections 4.2 and 4.5 and add the migration or infrastructure
   sections per [references/non-ui-specs.md](references/non-ui-specs.md)). Section
   4.11 (Roadmap) is a one-line pointer to the plan, and 4.10 (Testing) keeps
   the strategy only — the tasks, tests and estimates live in the plan, once.
   Then add:
   - **Decided** — the user's answers (Step 2, and later Step 6).
   - **Assumptions** — the assumed answers and the chosen approach (a user's
     pick is Decided).
   - **Open questions** — CRITICAL decisions not yet made, each with its
     recommended answer; the set is generated on that answer, marked
     provisional.
   - **Alternatives considered** — each rejected approach from Step 3.
   Open questions and Alternatives take the template's place and form.
   - **Prerequisites** — what the user must supply before the build: keys,
     accounts, devices, access. `None` when there is nothing.
   - **To file** — the exact entries Step 7 files, per family:
     reqs (requirements and constraints), arch (structure and data flow, each
     with its one-line why — except decisions an ADR carries, whose arch line
     Step 7 adds), design (look-and-feel and UX), tasks
     (`Build <feature> — docs/plan/<feature>.md`, except in spec-only mode,
     plus Out of Scope items marked for future consideration and non-critical
     owed decisions), and the ADR drafts — plus, on a re-run, every earlier
     `(planned)` decision now dropped: Step 7 removes its `(planned)`
     entries, and where `docs/adr/` exists its ADR is set `Deprecated`, the
     file kept.
   - **Review** — filled by Step 5, below any lines Step 3 saved.
2. **Companions** — only when the feature triggers them. Each IS its spec
   section: inside the spec while it fits about one screen, its own file
   beyond that, with the section pointing to the file (light mode: always
   inside the spec, unless it is already a file). Once a file, it stays
   a file; one a re-run no longer triggers is marked `No longer applies`,
   never deleted.

   | companion | spec section | file when large | trigger |
   |---|---|---|---|
   | API contract | 4.7 | `docs/spec/<feature>-api.md` | new endpoints or interfaces |
   | data and migration plan, with rollback | 4.4 and 4.12 | `docs/spec/<feature>-migration.md` | schema or stored-data changes |
   | threat model | 4.9 Security | `docs/spec/<feature>-security.md` | auth, secrets, user data or data that leaves the machine |
   | spike notes | 4.12 | `docs/spec/<feature>-spikes.md` | an assumption the build depends on is unverified |

   The API contract stays here until it is built; the README and API docs
   describe only built code, so `/spec update` writes them as the build lands
   (post-build mode writes them at once). Spikes are not run here: each
   becomes a plan task, ordered first.
3. **Plan** — invoke `superpowers:writing-plans` on the spec with these
   instructions (a user preference that overrides its defaults):
   - save to `<root>/docs/plan/<feature>.md` as ONE file; a large feature
     becomes phases inside it, never several plans;
   - the execution method is `/dev`, and the plan header names `/dev`
     in place of subagent-driven-development or executing-plans — those
     paths skip the doc capture that drops the `(planned)` markers;
   - every task carries a checkable "Done when"; the feature-level success
     criteria (Step 2, question 2) get acceptance tasks of their own; each
     phase carries an effort estimate (a flat plan: one for the whole plan);
   - every file the plan creates or changes carries a one-line reason, and
     every phase ends with the build and its tests green;
   - its plan review is answered by the Step 6 go, which approves the plan
     only — it does not stop for review and does not start any build;
     Step 8's offer replaces its own hand-off.

   Then set the plan's two header lines `/spec` owns: the Status line under
   the title, and the executor line naming `/dev` if writing-plans kept its
   own. **Every later re-invocation (Steps 5 and 6) repeats these instructions,
   adds the findings or changes, and re-sets the two lines.** writing-plans
   not installed → write the plan yourself to the same path: task-sized items,
   each with a "Done when", and estimates (per phase, or one for a flat plan);
   say so.

## Step 5: Review loop

READ `references/review.md` and run it: full mode, the review panel (§ Panel);
light mode, post-build mode and spec-only re-runs, § Single reviewer. It owns
closing findings, round 2 and the self-review fallback. Never skipped.

## Step 6: Go / no-go

ONE approval. Present first: any Critical finding still open, then each
Critical `fixed after round 2 — not re-reviewed` (light mode also: every fix round 2 did not see,
`fixed — not re-reviewed`); then the outputs written
(absolute paths); the review result (rounds, fixed, refuted, open); Decided, Assumptions (with the chosen
approach), Open questions (each with its recommended answer) and
Prerequisites; the To file list word for word; and what the go runs —
the filing and `/arch` (saying "creates" when no figure exists yet). Then
ASK for go, go with changes, no-go, drop it or walk (when the walk set of
`references/review.md` § Walk at the go is not empty). Only the
user's go counts — never declare one yourself.

- **Go** → every Open question the user did not answer takes its recommended
  answer; all of them move to Decided and lose their `provisional` mark, To
  file included; then Step 7.
- **Go with changes** (a different answer or assumption) → record it in
  Decided, apply it to the spec and companions, re-invoke writing-plans
  (Step 4.3), run ONE fresh review round (`references/review.md` § Agent tools'
  reviewer brief and write check) over ONLY the sections the change touched (the plan
  tasks it changed included), checked against the rest of
  the set — fix its Critical and Important findings, log the rest — and ask
  again.
- **Walk** → READ `references/review.md` § Walk at the go and run it; it
  ends at this question again.
- **No-go with gaps** → return to the step that owns each gap, then repeat
  Steps 5–6.
- **Drop it** → stop. A new feature's files stay `Status: draft — awaiting
  go`, so `/dev` is never offered for them. On a re-run, Step 4 has
  overwritten the approved version: READ `references/rerun.md` § Dropping a
  re-run, and tell the user how to get it back. Never restore or remove
  anything yourself.

## Step 7: File (on the go)

Run as one batch from `<root>`:

1. **Docs** — set every `Proposed` ADR in To file to `Status: Accepted`
   (a Deprecated one stays Deprecated), then file every To file entry per
   `references/docs.md` § Filing decisions — one writer per doc family (and,
   post-build, for the README, the API docs and the docstrings To file
   lists), all in ONE wave. Entries not built yet are marked
   `(planned)`; entries tagged `as-built` are filed as current state; dropped
   decisions lose their `(planned)` entries. The filing fails → stop: the set
   stays draft, and re-running Step 7 retries.
2. **Status** — once the filing succeeds, set the spec, companions and plan
   (not in spec-only mode) to `Status: approved <date>`.
3. **Figures** — after step 1, READ `references/figures.md`: `/arch` updates
   the diagrams (`/arch --all` creates them in a project that has none yet),
   with planned parts marked `(planned)` and never shown as live.

A figure step that fails, or whose skill is not installed, is reported
(`figure: stale — <why>`) and the batch goes on. Re-running Step 7 is safe:
entries are replaced in place. The To file list is what Step 5 reviewed;
`/arch`'s tools check the figures (archify's validation, the STE lint).

## Step 8: Close

Print the Final Package — READ `references/close.md` for its exact form: the
key points of what the spec decided (with the plan's estimate) first, then
status, every path, what was filed, figures, the review result, and what to
commit (outside git: keep) together.

Then OFFER `/dev` with the plan — never auto-run it; in spec-only mode,
instead name any plan tasks the user must remove for a dropped decision
before resuming `/dev`. `<root>` not a git
repo → say `/dev` needs one (it commits each task and keeps its ledger in
git) instead of offering it. Also offer, as applicable: the STE rewrite
proposals `/arch` returned (each needs its own yes), and — for a UI feature
whose design this run decided or changed (To file has design entries) —
Claude Code's built-in `/design` (research preview), when available, for
mockups; a mockup that changes the approved design needs a re-run.
