# spec — the project docs: filing, update, verify, changelog
<!-- author: shrix -->

READ at Step 7 (filing), in post-build mode, and for `/spec update`,
`/spec verify` and `/spec changelog`.

## The docs spec writes

- **Capture docs** — each a FAMILY of files, never one file: reqs
  (`docs/reqs.md`, `docs/reqs/**`, `REQUIREMENTS.md`, `docs/requirements/**`,
  `reqs-*.md`), arch (`arch.md`, `docs/arch.md`, `docs/arch/**`,
  `ARCHITECTURE.md`, per-module arch docs), design (`DESIGN.md`,
  `docs/design/**`), tasks (`tasks.md`, `docs/tasks/**`, `TODO.md`). Write in
  the member whose topic fits, following its structure. A family with no
  member yet gets only its canonical file: `docs/reqs.md`, `docs/arch.md`,
  `DESIGN.md`, `docs/tasks.md`.
- **ADRs** — in `docs/adr/` where the project keeps one, and the arch family
  still gets the one-line entry. Without one, never create `docs/adr/`
  unasked: the arch entry carries the decision, with its context and
  consequences in a line each.
- **README.md, API docs and user guides** — describe BUILT code only, so
  they are written post-build or by `update` as the code lands, never for a
  planned feature: README (user-facing features, setup, run commands), API
  docs where the project keeps them (`docs/api*`, `docs/refs/**`), user
  guides (`docs/user/**`), `docs/status.md` where kept.
- **Docstrings and code comments** — public APIs and logic that is not
  self-evident; never comments that repeat the code. `update` fixes the ones
  a change made wrong; post-build adds missing ones only in the source files
  To file lists, which the user's go approved.
- **CHANGELOG** — only on `/spec changelog`.
- ⚠️ **Generated pages are never hand-edited**: `docs/arch.html` (the hub) and
  the pages tools write into `docs/arch/` (`archify.*`, `ste100.*`). In the
  feature flow Step 7.3 runs `/arch`; `update` only names the pages its
  change made stale, and its caller regenerates them.

## Rules for every write and check

- Name the docs before touching them.
- Docs describe the current state: REPLACE the old description, never append
  beside it; retired names leave the body, history at most a terse endnote.
- A change that renames or alters a path, filename, flag, command or
  interface: grep every doc for the OLD form — Verify reports each hit,
  Update fixes it. Sweep by CONTENT, not file type: `.html`, `.json` and
  generated files drift as readily as `.md`. A doc naming something that no
  longer exists is a bug.
- Sections, steps and table rows go in the order the reader uses them;
  sets with no order of use rank most-relevant first.
- **One writer per file.** Independent docs are written in parallel — one
  writer per doc family, README and API docs, all in one wave.

## Filing decisions (Step 7, and decisions handed to `update`)

File every To file entry in its family: one entry in the member whose topic
fits, superseding an earlier entry in place except as below; an arch entry
carries its one-line why.

- **Not built yet → mark reqs, arch and design entries `(planned)`**; tasks
  entries and ADRs keep their own form (tasks are owed by definition, an ADR
  has its Status field). A planned entry never supersedes an as-built one; it
  sits beside it until an Update whose scope builds it drops the marker and
  supersedes the old entry then.
- **Tagged `as-built` → filed as current state**, no marker.
- **Dropped decision → its `(planned)` entries are removed**; where
  `docs/adr/` exists its ADR is set `Deprecated`, the file kept.
- An ADR already filed under the same title is updated, never filed twice.

## Update — `/spec update [scope]`

Sync the docs with code changes. **Scope**: a commit range (`BASE..HEAD`) or a
base SHA; with one, touch only the docs that changes in that range could have
staled, and never own drift that predates it. With none, everything not yet
pushed, working tree included:

```bash
# SCOPE: the caller's range or base SHA, else upstream, else HEAD
SCOPE="${SCOPE:-$(git rev-parse --verify -q '@{u}' >/dev/null && echo '@{u}' || echo HEAD)}"
# changed paths; untracked ones too unless SCOPE is a range
changed() { git diff --name-only "$SCOPE"; case "$SCOPE" in *..*) ;; *) git ls-files --others --exclude-standard ;; esac; }
changed | grep -Ev '(^|/)(tests?|specs?|__tests__)/|(^|/)(test_|conftest\.py)|[._](test|spec|cy|e2e-spec)\.|Tests?\.(java|kt|cs)$'
```

1. **Identify** what changed, plus any decisions handed in with it — those
   are filed per § Filing decisions.
2. **Impact** — which docs it affects (docstrings and comments in the
   changed code included), including `(planned)` entries this scope builds:
   drop their marker and supersede the as-built entry each sat beside. Each
   interface the scope added (as Verify's `undocumented` defines it) gets its
   doc — its docstring at least.
3. **Update** those docs (parallel per the rule above). Arch prose changed →
   name the generated pages now stale; the caller runs `/arch`.
4. **Check** each example and command the update touched.

## Verify — `/spec verify [scope]`

Check docs against the code; report drift, fix nothing (`update` fixes). Same
scope as Update; none → the whole project.

- **Already verified?** `bash ~/.agents/skills/_shared/scripts/checks.sh has
  docs [--base <base>]` exit 0 → this exact tree already passed: skip and say
  so in one line with its output — `skipped: docs — passed on this tree by
  /<skill> at <time>`. Else `checks.sh since docs [--base <base>]` exit 0
  prints the tree that last passed, the current fingerprint, then the paths
  changed between them: verify only each changed doc, and each doc naming a
  changed path or something in it (a function, flag, command or interface),
  reading the change with `git diff <passed> <current> -- <paths>`.
- **Checklist:**
  - reqs state what the project does NOW; arch describes the structure that
    shipped; design matches the experience as built; tasks list only work
    still owed
  - `(planned)` entries are owed work, not drift — list them; flag one only
    when its work shipped but the marker stayed
  - no doc names a file, flag, path or command that no longer exists
  - README: installation steps work; the quick start example runs; examples
    tested; every feature listed; links resolve
  - API docs: every endpoint, request/response shape and error code matches
  - **undocumented** — each interface no doc names, its own docstring
    counting as a doc; an interface any doc names (a README, an API doc) is
    documented without a docstring. Interfaces: a CLI command or flag, a skill invocation, an HTTP
    route, or a function or class that is exported (where the language marks
    exports; else top-level and non-underscore), outside the paths Update's
    filter drops and `**/fixtures/**`. A scoped run checks only interfaces
    the range added or changed, plus those whose only naming doc it changed;
    older gaps in the same files are listed as pre-existing. A `since` run
    also scans the code files changed between the two trees for these
  - **drift**, four types, each beyond the items above: a feature the docs
    describe that the code lacks; a data model missing fields the docs list
    (outside API docs); a value hard-coded where the docs say it is looked up
    or configured; a pattern or library other than the one the docs name
  - complex logic explained where it is not self-evident (a judgement)
  - **link nudge** — a doc naming a repo function, file or command without
    its path: list it with the path found
- **Record a clean pass** only when nothing is listed but link nudges, the
  complex-logic note, pre-existing gaps and `(planned)` entries listed as owed
  — those never block (a stale `(planned)` marker does). Record it with the fingerprint taken by `checks.sh fp` before
  the Verify began (after a `since`, the current one it printed):
  `checks.sh pass docs --by spec --tree <fp> [--base <base>]` (no `--base`
  for a whole-project Verify). A `BASE..HEAD` range leaves uncommitted files
  out, so it records only when nothing is uncommitted (the fingerprint equals
  `git rev-parse 'HEAD^{tree}'` and `checks.sh fp` left no file out), with
  `--base BASE`. The rules: `~/.agents/skills/_shared/references/checks.md`.

## Changelog — `/spec changelog`

Release notes from the commits since the last tag
(`git log $(git describe --tags --abbrev=0)..HEAD --oneline`), in Keep a
Changelog form — `## [Unreleased]` with Added / Changed / Fixed / Removed.
Conventional commits, changesets, breaking changes and migration guides:
`references/doc-guidance.md`.
