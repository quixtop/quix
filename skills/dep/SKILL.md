---
name: dep
author: shrix
description: "(shrix) Ship recent dev changes wherever they run — restart a service, build a client bundle, publish to a host — through a change-gated pipeline ending in a shipped table, a smoke-check widget and a deplog entry. Triggers on the bareword `dep` (also `dep <target>`, `dep server`/`srv`/`s`, `dep ext`/`extn`/`e`, `dep both`/`all`, `dep <target> force`) and on `deploy`/`go live`."
metadata:
  version: "2.1"
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
2. **Detected** — ONE parallel sweep for target signals (the presets in
   `references/targets.md` — local service, client bundle, hosted service,
   static site, package — and `references/platforms.md` for published ones).
   Unambiguous result → use it, and offer to record it in CLAUDE.md so step 1
   hits next time. A target that fits no preset is still a target: describe
   it by its triple and proceed.
3. **Ask** — only when detection finds nothing or is genuinely ambiguous. Ask
   once, then record the answer. Never ask twice for the same project.

Detection is a sweep, not a walk: probe every signal in one call. Never
re-derive targets mid-session, and never re-detect a project that recorded.

A target serves one or more **surfaces** — domains, environments, regions,
listings. Surfaces multiply the `prove` work, so they are batched (Concurrency).

## Variants
- `dep` (bare) — infer from what changed (see Inference)
- `dep <target>` — that target only, by its recorded name
- `dep all` / `dep both` — every target the gate matched
- `dep <target> force` — bypass the gate for that target only
- Built-in aliases: `server`/`srv`/`s`
  → the local-service target; `ext`/`extn`/`e` → the client-bundle target.
  In a project with exactly one target of that kind the alias is unambiguous;
  with several, it needs the recorded name.

## Pipeline (FIVE steps — every `dep`, every time)
Steps respect the change-gate; if the gate finds no changes at all, report
that honestly and stop — no later steps. Never skip a step silently: if one
legitimately doesn't apply, say which and why.

A check an earlier skill already passed on this exact tree is skipped, never
repeated: the check log, `~/.agents/skills/_shared/references/checks.md` (read
it before step 1; `checks.sh` below is
`bash ~/.agents/skills/_shared/scripts/checks.sh`). `<base>` is what `gate.sh
base` prints; with no stamp (exit 3) it is the commit before this session's
first commit, else `HEAD` — the set the gate covers. Every check-log question
and the calls to `/rev` and `/spec` use that `<base>`. The review questions
and the `/rev` call also carry `--paths <file>`, the gate's changed list
written to a file — `bash ~/.agents/skills/dep/scripts/gate.sh changed >
"$TMPDIR/dep-paths"`, plus what this session edited when it exits 3, written
repo-relative (`checks.sh` refuses absolute or `./` paths) — so a
review that covered those paths counts even when it started from a newer base,
such as `/rev`'s from the last push. Which tests run, and flaky ones:
`~/.agents/skills/_shared/references/test-runs.md`.

**Peers.** `/rev`, `/spec` and `/shipped` should be in your skills list.
One missing → name it and fall back: no `/rev` → a published target gets
one context-isolated review subagent, its Critical and Important findings fixed
in step 2; no `/spec` → step 1 does the doc sweep itself: grep every doc for
the OLD form of each renamed or changed path, filename, flag, command or
interface — by content, every file type — and step 2 fixes each hit before
shipping: generated docs regenerated, never hand-edited; retired names leave
the body (history only as an endnote); the docs named before they are
touched. No `/shipped` → the checklist prints as a table.

**Ask once.** Everything dep needs from the user — targets detection could not
settle, publish or local restart (§ Published Targets), and, when the changed
set touches auth, payments, secrets or user data (judged from its paths and
diff: login, session, token, password, payment, billing, secret, credential,
personal-data fields), whether to run `/claude-security` over the change
first — offered, never run unasked, since a scan is a multi-agent run — is
asked in one batch before step 1. On a yes the scan runs right after the ask,
while the user is still there for its own settings menu, and a Critical or
High finding blocks the ship like a red gate (step 3) until it is fixed or the
user says go. Then it runs to the report without stopping. The only mid-run
stops are safety gates: a red gate blocking the ship (step 3), a registry
publish's confirmation (`references/platforms.md`), and the asks of the `/rev`
it runs.

1. **Review + pre-deploy tests — ONE wave.** Both only read the current tree,
   so they start together — for a published target too, its `/rev` holding
   its fixes until the tests return; running them back-to-back wastes the
   whole of whichever finishes first.
   - *Review*: `checks.sh has review --base <base> --paths <file>` exit 0 →
     skipped, said so. Local targets get the quick inline pass (below),
     narrowed by `checks.sh since review --base <base> --paths <file>` to what
     changed after the last passed review. Published targets run
     `/rev <base> --paths <file>` instead — rev asks the same questions, so it
     reviews only what no pass covers — IN the wave
     (owner 12Oct26): its review dispatch and the tests below start together,
     and the wave's run is rev's baseline. rev applies its fixes only after
     those tests return — the suite never reads a half-edited tree — with a
     failing test before each, in at most two rounds (round 2 only after a
     Critical or security fix, or a fix adding logic), and runs the tests its
     fixes touch itself.
     It records no `tests` pass, so the wave's tests still run. It always gets a
     `<base>`, so it never stops at "nothing to review". Not a git repo (no base
     exists) → one context-isolated review subagent over what this session
     edited, its Critical and Important findings fixed in step 2.
   - *Tests*: this gate is the flow's ONE whole-system pass, for every
     target: the full suite once — every suite the project has, except
     end-to-end and full browser suites, which run only when the user asked —
     then the
     prove step (step 4). Never the narrow tests AND the full suite. Nothing
     ships without a full pass under 12 hours old — on this tree, or shrunk
     from it as below. `checks.sh has tests` exit 0 → the suite is skipped,
     said so. Else, with a full pass under 12 hours old
     (`checks.sh since tests`, `checks.md` § Before a check), the full suite
     shrinks to the tests the paths changed since then affect; a shrunken run records
     no `tests` pass. Neither → the full suite (none exist = say so).
     Published targets run the "important set" (a)–(c) below; a `tests`
     pass stands in for (a) only — it means every suite the project has ran
     green, end-to-end ones excepted — and (b) and (c) still run unless they
     are part of that suite; an end-to-end suite the user asked for this time
     runs whatever the log says. A
     failing test is re-run once alone: flaky by `test-runs.md`'s rule → still
     red for step 3, so the ship waits for the user's go with the test named,
     and it goes into the deplog's Pending; otherwise it is a real failure. A full-suite run that
     comes back green → `checks.sh pass tests --by dep --tree <the fp taken
     before it>`.
   - *Docs*: `/spec verify <base>`; drift it finds is fixed in step 2.
2. **Refactor** — apply the review's critical/important findings BEFORE
   anything ships, then re-run the tests those edits affect —
   tier the diff with `test-runs.md`'s table; a fix-only run, so it neither asks nor records
   (`checks.sh since tests` lists the paths when step 1's run recorded a pass,
   and an edit to what every test depends on still means the full suite) —
   the full suite itself runs once, in step 1. A published target's findings
   were `/rev`'s, in step 1, and rev already ran the tests its fixes touch:
   nothing is re-run here for them. Doc drift from step 1 is fixed here with
   `/spec update <base>`, and any generated doc it reports stale is
   regenerated.
   ⚠️ The ONE exception is the browser rung (c): it costs about a minute
   and proves nothing about a server-only edit, so re-run it only when a fix
   — dep's or `/rev`'s — actually touched page or visual code. "The affected
   tests always, the expensive rung on evidence" is the rule — not "re-run
   everything".
   Nits are listed for the user, never enacted here.
3. **Ship** — each matched target's `ship` action, in dependency order.
   BLOCKED by a red suite or an unresolved critical finding — this is the
   gate step 1 was feeding — and, for a published target, by a `/rev`
   that STOPPED or left any Critical or Important neither fixed nor refuted
   on the record — and by a `/claude-security` Critical or High finding
   (§ Ask once) that is neither fixed nor cleared by the user's go.
4. **Verify it took** — each matched target's `prove`. See Verification.
5. **Report** — printed last: the what-shipped table + the developer
   checklist (checkables; cumulative), AND a persistent key-result entry
   prepended into `docs/logs/deplogs.md` — both per § Report and deplog. When
   something shipped, the printed report ends, after the checklist, with one
   line of prose naming `/push` as the step that pushes, whenever the user
   chooses — never in the deplog, never as a command block. Then
   write the dep stamp when — and only when — the Change-Gate's stamp rule
   says so; that section is the single spec, this line just points at it.

## Concurrency (the default, not an optimization to remember)
Independent waits run TOGETHER; serial needs a stated reason. N independent
review slices of dep's own reviews ⇒ N agents in ONE message (`/rev` runs
once, over what no earlier review covers); independent suites in one wave;
every target × surface probed in ONE round; ship actions in parallel only where the
toolchain is proven safe, and then 3–4 at a time. ⚠️ Never parallelize ACROSS
a gate: review+tests → refactor → ship → verify stay strictly ordered. With
more than one target, surface, suite or slice, READ `references/concurrency.md`
first.

## Change-Gate (applies to ALL variants)
Only act on a target if its `owns` paths were modified since the last `dep`
(or since session start). No changes = skip that target, even if the user
named it. Report what was skipped and why so the user knows.

**"Since the last `dep`" is one command, not archaeology:**
`bash ~/.agents/skills/dep/scripts/gate.sh changed` (`gate.sh` below). It
prints the union of what was committed since the last dep's stamp, what is
uncommitted now and what the stamp lists, minus every file still byte-identical
to what that dep shipped — so work shipped uncommitted is not shipped again,
and a shipped file later reverted is. Paths come NUL-safe and unquoted; a
rename counts both paths, so a move out of an `owns` tree still triggers that
target. Exit 3 = no usable stamp: a first dep here, or its commit was rewritten
by a rebase, amend or squash. The list is then the uncommitted paths; add
what this session edited. Never rebuild the changed set from the session or
the deplog when the stamp can answer it. `gate.sh -h` has the rest.

**Stamping.** A dep that matched AT LEAST ONE target, shipped every one of
them, and passed every `prove` runs `gate.sh stamp` as its final act. An empty
match is a no-op, and "every target shipped" must never be read as vacuously
true of it. A first dep that finds nothing to ship stamps nothing: with no
stamp to diff from, stamping HEAD could bury committed-but-never-shipped work
from before the session.

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
oldest recorded `[stamp-hold]` sha with `gate.sh stamp <sha>`: the newest
commit every member provably serves.

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
  dead code introduced by the change, secret/injection slips — gaps that
  would break or leak in what ships, never style
- Skipped, or narrowed to what changed after the last passed review, per the
  check log asked with the gate's list (step 1)
- Apply only trivial, safe fixes directly (unused imports, debug prints,
  typos); structural refactors are suggested in text, never enacted here
- DOC DRIFT is a finding too, and `/spec` owns it: `verify <base>` in step
  1's wave, `update <base>` in step 2. Shipping code whose docs describe the
  previous form is a BUG, not a follow-up; this step is the gate.
- Critical findings BLOCK the ship — fix first, then continue
- This quick pass does NOT replace a full isolated code review at
  completion time; it exists to catch ship-wasting mistakes early
- LOCAL targets only — published targets go through `/rev` (see
  Published Targets)

## Published Targets
A target is **published** when shipping it puts code in front of anyone but
the developer — a hosted service, a static site, a package registry, a store
listing. Because that reaches other people, the FULL pipeline applies:
`/rev` over the part of the changed set no earlier review covers — a review
sized to the change and a failing test before each fix — not the quick pass.
Purely local targets are unaffected.

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
  (a) the full suite — every suite the project has (end-to-end and full
      browser suites only when the user asked), so the unit + runtime
      suites of every touched deployable — green at ship time or the ship is
      blocked (a `tests` pass on this tree in the check log counts, and a run
      shrunk from a full pass per step 1 stands in);
  (b) repo consistency-guard tests (config ⇄ code weld tests) if present;
  (c) a focused browser check of what changed, when a browser can see the
      change — that page or feature only (auth-gated pages: render the output
      offline from fixtures and screenshot that); end-to-end or full browser
      suites run only when the user explicitly asks;
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
Evidence before the claim, and the claim never outruns the evidence. Each target is proven by its own `prove`, never by
another's:
- **Restarted a service** — shipped with the project's own restart where it
  has one (`pm2 restart`, compose), else the old process stopped THEN started;
  never a foreground dev script backgrounded and called shipped (a start that
  exits non-zero looks healthy from outside). Confirm the NEW process is up (fresh PID, health
  endpoint, or a log tail showing the ready line — a bare port check cannot
  tell the new process from the old one still holding the port) before
  reporting completion. If it failed to start (port in use, syntax error, …), surface
  that error rather than reporting success: "port in use" is a FAILED ship,
  never routed around by another port or by killing what holds it.
- **Built a client bundle** — `dep` builds only and never loads or reloads
  it into a browser. The claim is "built", never "loaded" or
  "reloaded". Confirm the build exited clean and the output is newer than the
  sources; then say plainly that loading it is still the user's step, and put
  it in the developer checklist — never in `dep`'s success claim. Never
  assert on their behalf that it is running in a browser.
- **Published** — the evidence is the ship id (version id, release tag, digest)
  PLUS the live probes; a local check proves nothing about what is serving.
  Report failures as-is ("shipped, but the probe shows…"), never smoothed over.
- **Tests** — the gate's suite ran in step 1's wave (or was skipped or shrunk
  per the check log), and the tests any fix affects ran after it. If none
  exist, or a target isn't machine-testable (a UI needing a signed-in
  session, a visual no gate can stage), say so explicitly and defer it to the
  developer checklist.
- A red suite does NOT undo a completed ship — report both: "shipped, but
  tests fail:" with the output.

## Report and deplog (step 5)
READ `references/report.md` before step 5 prints anything. It holds the
what-shipped table, the developer checklist rendered as a widget (carried items
read from the previous deplog entry's **Pending**, never from memory), and the
exact shape of the entry in `docs/logs/deplogs.md`: newest first, a
`[DDMonYY/H.MMx]` timestamp, a summary ending in the ship id, then Deployed ·
Verified · Review · Pending. A no-op dep writes no entry. Never write a secret
value or PII into it.
