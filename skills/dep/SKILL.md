---
name: dep
author: shrix
description: "(shrix) Ship recent dev changes wherever they run — restart a service, build a client bundle, publish to a host — via a change-gated five-step pipeline ending in a shipped-table report + interactive smoke-check widget + deplog entry; resolves each repo's targets once. Triggers on the bareword `dep` (also `dep <target>`, `dep server`/`srv`/`s`, `dep ext`/`extn`/`e`, `dep both`/`all`, `dep <target> force`) and on `deploy`/`go live`."
metadata:
  version: "2.0"
  category: workflow
---

# dep — Ship Recent Dev Changes (any project, any target)

## Meaning
When the user types `dep` (alone or with a qualifier), they are asking to get
recent code changes running wherever that code lives. What that *means* is
project-specific — restart a service, build a client bundle, publish to a
host — so this skill never assumes a project shape. It resolves each repo's
**targets** once (below), then drives them through one pipeline.

## Targets — the one abstraction
A project has one or more **targets**. Each is a triple:

    owns   which paths belong to it        → feeds the change-gate
    ship   the action that makes it live   → restart / build / deploy / publish
    prove  the check that it IS live       → the evidence for step 4

Everything else in this skill derives from that: the gate is "whose `owns`
matched the diff", bare `dep` is "the matched set", `dep <name>` is one target
still gated, step 4 is each target's `prove`.

### Resolving targets — at most once per project, ever
1. **Recorded** — the project's CLAUDE.md already names its targets → zero
   exploration. This is the steady state and the common case.
2. **Detected** — ONE parallel sweep for target signals (see the presets
   below and `references/platforms.md` for published ones). Unambiguous result →
   use it, and offer to record it in CLAUDE.md so step 1 hits next time.
3. **Ask** — only when detection finds nothing or is genuinely ambiguous. Ask
   once, then record the answer. Never ask twice for the same project.

Detection is a sweep, not a walk: probe every signal in one call. Never
re-derive targets mid-session, and never re-detect a project that recorded.

### Presets — examples of the shape, NOT a closed list
A target that fits none of these is still a target; describe it by its triple
and proceed. Never refuse a project for not matching a preset.
- **local service** — dev script, `Procfile`, compose file, process manager →
  *ship* the project's own restart where it has one (`pm2 restart`, compose —
  they stop and start atomically, so forcing stop-then-start on them only adds
  downtime), else stop the old process THEN start · *prove* the NEW process:
  fresh PID, health endpoint, or ready-line. A port that answers proves only
  that *something* is listening — often the old process that never died, so
  "port in use" is a FAILED ship, not a warning to route around. Never
  background a foreground dev script and call it shipped: a start command that
  exits non-zero looks identical to a healthy one from the caller's side. No
  ship id — the report says "restarted".
- **client bundle** — extension manifest, build output dir → *ship* **build
  only** · *prove* the build succeeded and the output is fresh. `dep` does NOT
  load or reload the bundle into a browser: that needs a live browser, is
  stateful, and cannot be proven headlessly. Loading is the user's own step —
  "Load unpacked" in `chrome://extensions`, or their browser's reload — and
  belongs in the developer checklist, never in `dep`'s success claim.
  (No automated path exists: branded Chrome dropped `--load-extension` at
  137, and CDP `Extensions.loadUnpacked` no longer persists to the profile —
  verified 31Jul26 on Chrome 150 and Chrome for Testing 148.)
- **hosted service** — platform config in the repo → *ship* deploy ·
  *prove* live probe on every surface it serves
- **static site** — site config + publish dir → *ship* publish · *prove*
  fetch a marker from the live URL
- **package** — registry manifest + version bump → *ship* publish · *prove*
  the new version resolves from the registry

A target serves one or more **surfaces** — domains, environments, regions,
listings. Surfaces multiply the `prove` work, so they are batched (Concurrency).

## Variants
- `dep` (bare) — infer from what changed (see Inference)
- `dep <target>` — that target only, by its recorded name
- `dep all` / `dep both` — every target the gate matched
- `dep <target> force` — bypass the gate for that target only
- Built-in aliases, so existing muscle memory keeps working: `server`/`srv`/`s`
  → the local-service target; `ext`/`extn`/`e` → the client-bundle target.
  In a project with exactly one target of that kind the alias is unambiguous;
  with several, it needs the recorded name.

## Pipeline (FIVE steps — every `dep`, every time)
Steps respect the change-gate; if the gate finds no changes at all, report
that honestly and stop — no later steps. Never skip a step silently: if one
legitimately doesn't apply, say which and why.
1. **Review + pre-deploy tests — ONE wave.** Both only read the current
   tree, so they start together; running them back-to-back wastes the whole
   of whichever finishes first.
   - *Review*: local targets get the quick inline pass (below). Published
     targets get the FULL context-isolated subagent review — putting code in
     front of other people earns the formal gate.
   - *Tests*: the relevant automated checks, narrowest first (none exist =
     say so). Published targets run the "important set" (a)–(c) below.
2. **Refactor** — apply the review's critical/important findings BEFORE
   anything ships, then re-run. Narrow to the suites those edits touched only
   where the full gate costs MINUTES; where it costs seconds, just re-run it —
   deciding what a shared-library edit "touched" is itself judgement, and a
   wrong call ships untested code to save a few seconds.
   ⚠️ The ONE exception is the browser/visual rung (c): it costs about a minute
   and proves nothing about a server-only edit, so re-run it only when the
   refactor actually touched page or visual code. "Re-run the cheap gate always,
   the expensive rung on evidence" is the rule — not "re-run everything".
   Nits are listed for the user, never enacted here.
3. **Ship** — each matched target's `ship` action, in dependency order.
   BLOCKED by a red suite or an unresolved critical finding — this is the
   gate step 1 was feeding.
4. **Verify it took** — each matched target's `prove`. See Verification.
5. **Report** — printed last: the what-shipped table + the developer
   checklist, checkables; cumulative — see Dep Report), AND a persistent
   key-result entry prepended into `docs/logs/deplogs.md` (see Deplog for the
   exact insert point). Then stamp `.git/dep-stamp` when — and only when — the
   Change-Gate's stamp rule says so; that section is the single spec, this line
   just points at it.

## Concurrency (the default, not an optimization to remember)
A `dep` is mostly *waiting* — on suites, on bundlers, on propagation, on
subagents. Independent waits run TOGETHER; serial is the exception and needs a
stated reason. Cost scales with targets × surfaces, so batching is what keeps
a large repo tractable and a small one instant.
- **Reviews** — N independent slices ⇒ **N agents in ONE message**, never one
  agent asked to walk them in turn. A single agent reads slice 2 only after
  finishing slice 1, so its wall-clock is the SUM where N agents' is the MAX.
  The review is typically the LONGEST step in a dep — measured at ~⅓ of one —
  which makes splitting it the single biggest lever on how long a dep takes.
  Split by what can be judged independently: per target, per slice, per concern.
  Same when one review would otherwise cover several targets.
- **Suites** — independent suites (separate runners/dirs) run in one wave. A
  project script that walks them serially is worth fixing *at the script*,
  not working around here.
- **Probes** — every target × surface in ONE round; a convergence poll
  re-probes the whole set each round. Never walk surfaces one at a time.
- **Ship actions** — parallel where the toolchain is proven safe; serial where
  it is not. Before defaulting to serial, check whether the hazard has a known
  REMOVAL. The classic trap is a shared package-manager cache lock: concurrent
  invocations race it and the losers abort — but invoking the locally-installed
  binary directly does no package resolution at all, which eliminates the race
  rather than tiptoeing around it. Serial-by-reflex on a fleet of deployables is
  a long, avoidable wait.
  ⚠️ Even with the hazard gone, batch MODESTLY (3–4 at a time), not N-wide:
  provider APIs throttle or bot-challenge a burst, and one rejected ship costs
  far more than the seconds a wider fan-out would have saved.
- **Never parallelize ACROSS a gate.** review+tests → refactor → ship →
  verify stay strictly ordered. Concurrency lives *inside* a step, never
  through one.

## Change-Gate (applies to ALL variants)
Only act on a target if its `owns` paths were modified since the last `dep`
(or since session start). No changes = skip that target, even if the user
named it. Report what was skipped and why so the user knows.

**Resolving "since the last `dep`" — one command, not archaeology.** A dep that
matched AT LEAST ONE target, shipped every one of them, and passed every
`prove` writes HEAD's sha to `.git/dep-stamp` as its final act — an empty
match is a no-op, and "every target shipped" must never be read as vacuously
true of it
(inside `.git/`, so it never needs gitignoring — same trick as push's
`.git/push-rel-branch`). The gate then reads, in one call:

    base=$(git rev-parse --verify --quiet \
             "$(cat .git/dep-stamp 2>/dev/null)^{commit}" || echo HEAD)
    git diff --name-only "$base"..HEAD
    git status --porcelain

The changed set is the union: committed-since-stamp ∪ still-uncommitted. No
stamp yet (first dep in this repo) → fall back to the working tree plus what
this session edited, and — if that dep actually shipped everything it matched —
write the stamp at the end so the NEXT dep is cheap. (A first dep that finds
nothing to ship stamps nothing, same as any no-op: with no stamp to diff from,
stamping HEAD could bury committed-but-never-shipped work from before the
session.)
Never reconstruct the changed set by re-reading the session or the deplog when
the stamp can answer it — that archaeology is the slowest part of a small dep.

⚠️ **A stamp the repo can no longer resolve must DEGRADE, not error.** Rebase,
amend, or a squash (push squashes `checkpoint:` commits) rewrites the sha the
last dep recorded; `git diff <gone-sha>..HEAD` then exits non-zero and takes the
whole gate down with it. Verify the sha resolves before using it — absent and
unresolvable fall back the same way.

⚠️ **A PARTIAL dep does not stamp — and "matched set" means everything whose
`owns` changed, not just what THIS run acted on.** If any matched target failed
to ship, failed its `prove`, or was left out of scope by a `dep <target>` /
`force` invocation while its changes stand, leave the previous stamp untouched
and say so in the report. A target skipped by scoping did not *fail* — but
stamping over it tells the NEXT dep it has nothing to ship, which is the same
silent burial as stamping over a failure, and equally invisible from the
outside. The rule is therefore all-or-nothing over the CHANGED set: stamp only
when every target the diff implicates is live with those changes. (When a
LATER action completes a previously-partial set, stamp the newest commit the
whole set actually serves — which may be older than HEAD if unshipped work has
landed in the repo since.) For that to be COMPUTABLE, a partial dep records
the sha its shipped targets serve as a `[stamp-hold <sha>]` bullet in its
deplog entry's Pending — the completing dep reads it from the FILE (never
from session memory, same rule as the `[chk]` checkables) and stamps the
oldest recorded `[stamp-hold]` sha: the newest commit every member provably
serves.

**Not a git repo**: there is nowhere to stamp, so the gate is what this session
edited, and `dep` says so plainly rather than implying a diff it cannot compute.
Everything downstream — targets, pipeline, verification, deplog — is unchanged;
only the gate's evidence is weaker, and the report must not pretend otherwise.

Classifying the changed set:
- Attribute each path to the target whose `owns` covers it. A path can belong
  to more than one target — shared library code feeds every target that
  bundles it, and those all need shipping.
- A target's own config file (platform config, manifest, compose file) counts
  as that target's code.
- Paths owned by nothing (docs, comments-only, unrelated files) → no target
  needs shipping; tell the user no actionable changes were detected.

## Inference (for bare `dep`)
The matched set from the change-gate IS the answer:
- One target matched → ship it
- Several matched → ship all of them in dependency order
- Nothing matched → report "no code changes since last `dep`" and stop

## Explicit Variants
Naming a target expresses *intent*, but the change-gate still applies. If the
user says `dep all` and only one target changed, ship that one and explicitly
note which were skipped and why. If they want to ship anyway, `dep <target>
force` bypasses the gate for that target — never silently ship something that
didn't change.

## Quick Review / Refactor (before shipping)
- Scope: ONLY the files changed since the last `dep` (the same set the
  change-gate identified)
- Fast inline pass over the diff: obvious bugs, leftover debug output,
  dead code introduced by the change, secret/injection slips
- Apply only trivial, safe fixes directly (unused imports, debug prints,
  typos); structural refactors are suggested in text, never enacted here
- DOC DRIFT is a review finding: when the diff renames or changes a path,
  filename, flag, command, or interface, grep the docs for the OLD form and
  fix every hit before shipping. Scope that sweep by CONTENT, not file type
  — `.html`, `.json`, and generated files drift just as readily as `.md`.
  Shipping code whose docs describe the previous form is a BUG, not a
  follow-up (`docs-conventions` owns the rule; this is the gate).
- Critical findings BLOCK the ship — fix first, then continue
- This quick pass does NOT replace the formal code-review rule at
  completion time; it exists to catch ship-wasting mistakes early
- LOCAL targets only — published targets escalate to the full isolated
  review (see Published Targets)

## Published Targets
A target is **published** when shipping it puts code in front of anyone but
the developer — a hosted service, a static site, a package registry, a store
listing. Because that reaches other people, the FULL pipeline applies (formal
isolated review, not the quick pass). Purely local targets are unaffected.

- **Ship only on the word**: `dep` / "deploy" / "go live" is the ONLY trigger
  — never publish unprompted, never fold a publish into an unrelated task. One
  `dep` covers its whole verification loop: a fix for a failure found in THIS
  dep's live checks may re-ship without a fresh ask (this is ROLL-FORWARD,
  the default the rollback rule below refers to).
- **Record the outgoing ship id BEFORE shipping.** A published target that fails
  its `prove` is ALREADY serving the bad build, so the live question is "what do
  we go back to" — and that answer has to be captured while the old version is
  still the running one; afterwards it is a dashboard hunt under pressure.
  Roll-forward stays the default (see above); rollback is the escape for when the
  fix isn't immediate. Note the previous id in the deplog beside the new one.
- **Multiple deployables**: each ships from its own directory/config; ship
  every one whose code changed — including ones that merely *import* changed
  shared code, since bundlers inline it. Order by dependency: providers before
  consumers.
- **The important set — deliberately nothing more.** (a)–(c) are the
  PRE-ship gate that runs in step 1's wave; (d) is step 4, after it lands:
  (a) unit + runtime suites for every touched deployable — green at ship time
      or the ship is blocked;
  (b) repo consistency-guard tests (config ⇄ code weld tests) if present;
  (c) headless-browser behavioral/visual checks when the change is visual
      (auth-gated pages: render the output offline from fixtures and
      screenshot that);
  (d) **live verification** — prove the NEW code serves: probe a marker that
      flips with the change (a new route's 404→401/200, a header, a string in
      the page, a resolvable version) on EVERY surface the target serves, plus
      quick regression probes of the core paths. All surfaces per round (see
      Concurrency), never one at a time.
- **Platform mechanics** — per-platform commands, flags, and propagation
  behavior live in `references/platforms.md`. Read it only when a published
  target is actually in play.
- **Local-dev ambiguity**: if the user is actively iterating against a local
  dev server for a published target, ask once at the first `dep` of the
  session whether they mean publish or local restart; remember the answer.

## Verification & Honesty About What Was Done (step 4)
Evidence before the claim, and the claim never outruns the evidence (per the
verification rule). Each target is proven by its own `prove`, never by
another's:
- **Restarted a service** — confirm the NEW process is up (fresh PID, health
  endpoint, or a log tail showing the ready line — a bare port check cannot
  tell the new process from the old one still holding the port) before
  reporting completion. If it failed to start (port in use, syntax error, …), surface
  that error rather than reporting success.
- **Built a client bundle** — the claim is "built", never "loaded" or
  "reloaded". Confirm the build exited clean and the output is newer than the
  sources; then say plainly that loading it is still the user's step. Never
  assert on their behalf that it is running in a browser.
- **Published** — the evidence is the ship id (version id, release tag, digest)
  PLUS the live probes; a local check proves nothing about what is serving.
  Report failures as-is ("shipped, but the probe shows…"), never smoothed over.
- **Tests** — the narrowest relevant ones already ran in step 1's wave and
  again after any refactor. If none exist, or a target isn't machine-testable
  (a UI needing a signed-in session, a visual no gate can stage), say so
  explicitly and defer it to the developer checklist.
- A red suite does NOT undo a completed ship — report both: "shipped, but
  tests fail:" with the output.

## Dep Report — one table + the checklist widget
A `dep` is a completion, so it ends with the what-shipped table (rendering per the
`info-enhancement` rule), then the developer checklist rendered AS a widget:

1. **What shipped** — the completion status table, exactly per the `completion-summary-table` rule
   in `verification.md`; no dep-specific spec — just use each target's ship id as the status column
   (version id, tag, digest; "restarted" where a target has no id).
2. **Developer checklist** (checkables, printed LAST) — the dep-unique set, rendered as the
   widget in (3), not as a table: one row per item, its text carrying page/feature, the action
   that proves it works, and the expected result. One row per mod since the
   last `dep`; flag whatever automation couldn't verify or the gate skipped; scope is cumulative —
   carry forward earlier items the user hasn't confirmed testing yet (until smoked).
   ⚠️ Read those carried items from the PREVIOUS deplog entry's **Pending**, never from memory of the
   session. A checklist that depends on recall is lost to the next compaction — the same archaeology
   `.git/dep-stamp` exists to kill, solved there for the CHANGED set and left unsolved here for the
   CHECKABLE set. Reading it from the file also means the user can see what is outstanding without
   asking. Items they confirm are dropped; the rest are re-listed and land in this dep's own Pending.

   **Confirmation is a FILE, not a chat message.** Drop an item when
   `docs/logs/verilog.md` records it under its dep — never because it was mentioned
   in conversation, which the next compaction loses. Same source-of-truth rule
   as the carried items above.

3. **Checklist widget** — the developer checklist (2) is rendered AS an
   interactive `show_widget`, not as a markdown table. One rendering, never
   both: the widget carries the same rows and can be acted on, so printing a
   table beside it re-lists the same checks twice. Each row's text is the
   `[chk]` phrase itself, which already reads as action-plus-expectation. Spec
   (three-state marking, full-state reporting, hidden IDs, the verilog format) lives
   in the `shipped` skill under "Widget mode", "Columns" and "Recording a
   report" — one definition, both entry points. A checkable's position in this
   dep's list IS its ID.
   `dep` shows this dep's checks while they're fresh; `/shipped -wu` is the
   catch-up view across deps. Both read and write the same file.

## Deplog (persistent key-result log)
Every `dep` that actually did something also records a key-result entry in
`docs/logs/deplogs.md` — the durable record of what shipped. A no-op dep
(change-gate found nothing) writes **no entry**.

- **File / auto-detect**: `docs/logs/deplogs.md`. If missing, create it with a
  header from the project name (git remote basename or dir): `# <ProjectName> Deplog`
  followed by a dashed underline — then proceed.
- **Insert newest-first**: prepend the entry directly after the header block;
  reverse-chronological. **No `---` separators**. **Exactly one blank line
  BETWEEN entries; NO blank lines WITHIN an entry** — the timestamp, summary,
  and every section run tight, back-to-back.
- **Timestamp**: `[DDMonYY/H.MMx]` (x = `a`/`p`), the time the dep ran — a single
  timestamp, never a range. E.g. `[12Jul26/1.07p]`.
- **Entry shape**: the timestamp line, then a `>` **bold summary** line — what
  this dep shipped, lowercase prose (acronyms/proper nouns kept capitalized),
  ending with the **ship id** `(v <sha>)` — with the outgoing id beside it as
  `(v <sha>, prev <sha>)` when the rollback rule captured one; that pair is the
  ONE exception to ids never repeating — and, for published targets, the
  destination `→ <host> (<env>)` (env = prod/staging/… — the highest-stakes fact).
  A dep of SEVERAL deployables puts the LEAD deployable's id in the summary;
  the rest ride the first **Deployed** bullet, one id each — the summary never
  carries more than one id (plus its `prev`).
  A local-only dep has no id — its summary ends `(restarted)` instead.
  The id rides the summary ONCE — never repeated on individual bullets. Then
  the grouped sections below, with no blank line before or between them.
- **Grouped sections** — each is a `**Bold**` header line immediately followed by
  its `- ` bullets (`- ` markers, never `• ` U+2022; no per-bullet timestamps; no
  per-bullet version). Order, **omitting any section with nothing to report**
  (only Deployed is effectively always present, so a clean deploy stays terse):
    1. **Deployed** — the substance: the itemized changes / features / fixes this
       dep shipped, one bullet per notable change. Note the target surfaces/env on
       the header line when useful, e.g. `**Deployed** (both surfaces — …)`.
    2. **Verified** — the proof it works. Two facets, kept under this one header
       when light, or split into their own `**Tests**` / `**Live**` headers
       when either is substantial:
         - **Tests** — local suite outcome (framework, counts, pass/fail).
         - **Live** — probing what is *actually serving* (not localhost): the
           ship propagated and responds correctly where it counts.
    3. **Review** — the quality gate: context-isolated review outcome (passed, or
       findings + how they were resolved). Omit if no review ran.
    4. **Pending** — the residue, LAST: dormant-until-configured, deferred items,
       known issues / failures, follow-ups, and **every developer-checklist item the
       user has not yet confirmed** — checkables prefixed `[chk]` and keeping their
       row's action + expected result, so the next dep REBUILDS the table instead of
       guessing which residue bullets were checkables. A PARTIAL dep also records
       `[stamp-hold <sha>]` here (see Change-Gate) so the completing dep can stamp
       from the file. This section is what the NEXT dep reads to
       rebuild its cumulative checklist (see Dep Report), so an item omitted here is
       an item forgotten. Omitted entirely when genuinely clean.
  A bullet is a terse one-liner; add an **indented continuation line** beneath it
  ONLY when the one-liner isn't self-evident — not on every bullet. This grouped
  shape intentionally diverges from the flat chatlog bullet list — deploy results
  are categorical, so grouping them reads far faster.
- **Project-scoped**: only *this* repo's dep — never log another project's or
  off-project work.
- **Secret-redaction (mandatory)**: never write literal secret values (API keys,
  JWTs, tokens, passwords, DB creds, PEM blocks) or PII into a bullet. Describe
  intent, not value; when in doubt, redact.
