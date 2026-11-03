# Profiles

Pick the profile by its heading or "Detected by" line; the legend names the rest.

- **Precedence:** the most specific match sets the goal — `skill`, `rules`,
  `architecture`, `hooks` beat the catch-alls `docs`, `code`, `shell`,
  `config`. Gates are the UNION of every matching profile; none is dropped.
- **Several parts** (a skill with scripts, a repo): one contract per part;
  coupled parts are optimized together.

Legend: **goal** default goal · **gates** hard gates · **measure** how to
measure · **moves** safe moves, biggest first · **guard** what holds the gain
· **never** what the profile forbids.

## Where a fix lives — rules, skills, prompts, Claude Code setup
Pick the cheapest form that fixes what the evidence shows:

| the evidence shows | the fix's form |
|---|---|
| the same mechanical step redone every run (extract, convert, check) | a script, with its inputs, outputs and failure behaviour |
| a multi-step procedure that only some situations need | on-demand text (a `references/` or `rules-ref` file), its trigger named in the always-on text |
| ordinary order or wording | short always-on text |
| a clear rule skipped again and again — repeated evidence, never one miss | a hook or a gate that never blocks valid work: a proposal for its own yes, never applied in the run |
| one stochastic miss, once | nothing — that is noise (`judging.md` § Held-out samples) |

A form that creates a new file needs its folder in the contract's editable
surface (SKILL.md §2); a form whose path the contract does not cover is a
proposal, not an edit. Where the profile's gates forbid the form — rule text
moves only verbatim, so a rule turned into a script — or the form is a new
skill, it is a proposal for its own yes. Always-on text costs tokens on
every turn: a change that adds some names what it cuts, or the report names
the net increase.

---

## A. Code and scripts

### code
Detected by a source-file extension.
- **goal** faster or clearer, identical behaviour
- **gates** the tests the batch affects green against the baseline (tests that
  already failed are not attributed to the run; the full suite only on the
  user's ask); build and lint pass
- **measure** a profiler or flame graph for speed; cognitive complexity and
  churn × complexity hotspots for clarity
- **moves** fix the hot path the profiler shows; flatten nesting; name
  intermediates. Clarity beats brevity — no nested ternaries, keep
  abstractions that help. Dead code is `/rev`'s: name what an analyser (not
  grep) shows as dead and hand it over, rather than deleting it here
- **guard** a CI benchmark compared to history, or a lint complexity cap

### shell
Detected by `.sh` or a shell shebang.
- **goal** fewer forks and subshells, faster
- **gates** `shellcheck` clean; same stdout and exit code on fixtures
- **measure** `hyperfine`
- **moves** builtins over external commands; one pass over data instead of pipelines of `grep | sed | awk`
- **guard** a fixture test plus `shellcheck` in CI

### sql / schema
Detected by `.sql`, migrations, or query strings.
- **goal** less time and less I/O
- **gates** identical result checksum on a fixture database; any write runs inside `BEGIN … ROLLBACK`
- **measure** `EXPLAIN (ANALYZE, BUFFERS)`, `pg_stat_statements`
- **moves** the right index; avoid N+1; select only needed columns; paginate
- **guard** a query-time or plan assertion in the test suite

### tests
Detected by test directories.
- **goal** a faster suite, fewer flaky tests
- **gates** the same set passes; mutation score no lower
- **measure** `--durations`, rerun statistics for flakiness
- **moves** parallelise; shrink large tests (larger tests are flakier); quarantine flaky ones with a ticket
- **guard** a suite-time budget in CI

### deps
Detected by manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, …).
- **goal** fewer and lighter dependencies
- **gates** build and the tests the batch affects green — a manifest or
  lockfile change affects every test
- **measure** `knip`, `deptry`, `cargo-machete`, `vulture`
- **moves** drop unused dependencies; replace heavy ones used for one function
- **guard** the analyser in CI

### build
Detected by a build config (bundler, Makefile, `tsconfig`).
- **goal** faster builds, smaller output
- **gates** the built artifacts behave the same; same entry points
- **measure** build wall time; output bytes (brotli)
- **moves** caching, incremental builds, drop unused entry points
- **guard** a build-time or `size-limit` budget

---

## B. Markdown and text

### docs
Detected by `.md`, README, `docs/` — the catch-all for markdown.
- **goal** the reader finds the answer faster; each thing said once
- **gates** no fact lost (diff proof); every link and path exists
- **measure** a fresh subagent answers task questions from the doc, before and after; readability scores only as a tripwire
- **moves** current state first, history last; one term per concept; active voice; mixed documentation types (tutorial vs reference) separated
- **guard** a link check; a template for new docs

### rules — `~/.claude/rules`, CLAUDE.md, AGENTS.md, MEMORY.md
- **goal** fewer tokens loaded per turn, same behaviour
- **gates** no rule lost; moved text verbatim (diff proof); no new contradiction; stays under ~200 lines per file
- **measure** tokens per file and per working directory (what each directory actually loads); `/context`
- **moves** classify each block Essential (stays inline) / Reference (moved to an on-demand `<topic>.md` where the rules already point, leaving a 3–5 sentence summary with the specifics and a pointer that says WHEN to read it) / Redundant (removed); dedupe across levels, keeping each rule at the highest level where it applies; flag misplaced content (project rules in global files, global rules buried in a repo); stable content first, changing content last, for prompt caching
- **never** move content that is used in most sessions, that CI greps for, or whose home is unclear — keep it inline; a stable rule is not stale because it is old
- **guard** a line cap per file

### skill — `SKILL.md`
- **goal** triggers exactly when it should; lean body
- **gates** frontmatter valid; `name` == directory; description ≤ min(1024, `skillListingMaxDescChars` in `~/.claude/settings.json`, else 1536) chars; trigger evals no worse
- **measure** realistic queries including near-misses that must NOT trigger (`judging.md` § Held-out samples)
- **moves** the description says WHEN to use it, in the user's words; never paste keywords from failed queries; heavy detail moves to `references/`; a helper every run rebuilds ships as a script
- **guard** the eval set kept beside the skill

### prompt — agent definitions, prompt files, system prompts
- **goal** better task output at lower token cost
- **gates** outputs on held-out sample inputs no worse
- **measure** run it on the samples; count input and output tokens
- **moves** lean text; explain the reason instead of ALL-CAPS commands; stable prefix first, variable data last (cache hits); fewer output tokens
- **guard** the sample set and a token budget

### message — email, chat, PR description
- **goal** one read leads to the right action
- **gates** every ask, date and number kept
- **measure** does the bottom line come first; does it fit one screen
- **moves** bottom line up front; a subject with the key word; one ask per message
- **guard** none automatable — say so

### slides
Detected by `.pptx`, `.key`, slide markdown.
- **goal** one message per slide
- **gates** no fact lost
- **moves** sentence headlines; a visual instead of bullets where the content is visual
- **guard** a template

---

## C. Design

### ui visual
Detected by html / css / jsx / design tokens, with a clarity or consistency goal.
- **goal** clearer hierarchy, consistent system, less noise
- **gates** function intact; WCAG 2.2 AA (contrast, labels, target size) no worse
- **measure** screenshot comparison judged pairwise; element and colour counts; token consistency; `axe-core` paired with a manual check (coverage in `dimensions.md`)
- **moves** clearer hierarchy; consistent spacing and type scale; tighter copy that says the same thing; remove only pure duplication or decoration with no function — never a feature, content or flow (that is a redesign)
- **guard** `axe` in CI; design tokens as the only source of values

### ui performance
A web UI with a speed goal — the checklist is `ui-performance.md`.
- **gates** function and accessibility intact
- **measure** Core Web Vitals at p75 (thresholds in `dimensions.md`), lab and field labelled separately
- **guard** Lighthouse CI assertions over ≥ 3 runs (median); a timing budget first, byte budgets second

### architecture and diagrams
Detected by arch files (`arch.md`, `docs/arch/**`, `ARCHITECTURE.md`), ADRs, Mermaid / diagram sources.
- **goal** fewer components and crossings for the same capability; clear seams
- **gates** every requirement still maps to a component; no behaviour change implied
- **measure** components, dependency edges, cycles; for diagrams, crossings and label legibility
- **moves** name boundaries by responsibility. Merging a one-caller component or breaking a cycle is a separate proposal, applied only on its own yes
- **guard** a dependency-rule check where the stack has one

### api surface
Detected by OpenAPI, `.proto`, a package's exports.
- **goal** a more consistent, better-documented surface — same capabilities
- **gates** nothing removed or changed (every observable behaviour is someone's contract)
- **measure** naming consistency; documented vs undocumented symbols
- **moves** consistent naming through aliases; clearer docs. Removing or deprecating anything is a redesign — a separate proposal
- **guard** a compatibility check in CI

---

## D. Claude Code setup

### settings and permissions — `settings*.json`
- **goal** fewer interruptions inside the project, the same protection outside it
- **gates** parses; effective behaviour identical by semantic diff (`jq` flattening, `dyff`); never drop a deny or ask rule for tidiness
- **measure** rule counts; duplicates across global / local / project files; rules shadowed by broader ones; rules with no effect in the active mode; asks actually shown — asks per 100 tool calls and the top ask patterns since the last settings change: `perm-asks -v` when installed (it splits at the last commit that changed `~/.claude/settings.json`; `-s <time>` for a change it can't see), else count the tool results in `~/.claude/projects/**/*.jsonl` whose `permissionDecision.source` is `user_temporary` or `user_reject`, or `user_permanent` without `reasonType: rule`
- **moves** remove duplicates and shadowed or dead rules; fix path prefixes (`//` absolute, `/` settings-relative); for each top ask pattern, one proposal that waits for its own yes — **allow** it (trivial and read-only, never a pattern that runs arbitrary code; Claude Code's `/fewer-permission-prompts` covers read-only Bash and MCP), **fix the cause** (the workaround that triggered it, e.g. a sandbox block that sent the command to the terminal tool), or **keep** the ask and say why
- **guard** a settings audit script, or none — say so; the asks-per-100 number becomes the floor for the next run

### hooks
Detected by `~/.claude/hooks`, `.claude/hooks`.
- **goal** less latency per invocation of its event (every tool call for
  `PreToolUse` / `PostToolUse`, every prompt for `UserPromptSubmit`)
- **gates** every decision the hook returns is unchanged on a replay of real
  inputs; with none recorded, fixtures that cover each branch; output that
  depends on the environment is tested with that environment stubbed
- **measure** milliseconds per invocation; subprocesses spawned
- **moves** fewer forks; exit early on the common case; one parse of the input
- **never** edit a security guard hook (delete, git, path-case, secret scanning) to make it faster — measure and report only
- **guard** the replay suite

### context load — skills, MCP servers, plugins, CLAUDE.md
- **goal** fewer tokens per turn, more cache hits
- **gates** no guard dropped; evals no worse
- **measure** `/context`; cache-hit %; per-item token weight
- **moves** move reference detail out of always-loaded files; stable content first; trim descriptions to the same meaning. Disabling an unused MCP server, plugin or skill removes a capability — list it as a separate proposal, applied only on its own yes
- **guard** a token budget per turn; a line cap on CLAUDE.md

---

## E. Infrastructure and config

### config — json / yaml / toml
- **goal** redundancy removed, same meaning
- **gates** parses; semantic diff shows no effective change
- **moves** remove duplicates and entries that restate the default
- **guard** schema validation

### container — Dockerfile
- **goal** smaller image, faster rebuild
- **gates** builds; an entrypoint smoke test passes
- **measure** image size, `dive`, `hadolint`
- **moves** multi-stage builds; order layers by change frequency; slim base images
- **guard** an image-size budget in CI

### ci — `.github/workflows` and similar
- **goal** shorter wall time
- **gates** the same jobs run for the same paths
- **measure** run durations; `actionlint`, `zizmor`
- **moves** caching; path filters; parallel jobs
- **never** weaken a security finding — report it
- **guard** a duration alert

### repo
Detected by `.git`.
- **goal** a smaller clone
- **gates** no content lost
- **measure** `git-sizer` (analysis only)
- **moves** report history rewrites; never apply them — they are irreversible
- **guard** a `git-sizer` threshold check, or none — say so

### disk — caches, logs, histories
Detected by a directory of generated, cached or accumulated files.
- **goal** space back
- **gates** every removal is listed with its size and needs the user's yes; only rebuildable content the user OWNS qualifies — external caches (plugin versions, third-party build output) need a separate yes for that item; histories other tools read (transcripts, edit history) are never deleted — a retention setting is proposed instead
- **measure** `du -sk`; file counts; age distribution
- **moves** clear rebuildable build caches and superseded versions; set a retention period; every removal on yes
- **guard** the retention setting, or none — say so

---

## F. Data and assets

### data file — csv / json / parquet
- **gates** same row count, sorted checksum and schema
- **measure** bytes; read time
- **moves** columnar formats for analytics; compression; sensible row groups
- **guard** a schema and row-count check where the data is produced

### image — png / jpg / webp / avif / svg
- **gates** same dimensions; lossless moves stay pixel-identical; a lossy move needs a yes
- **measure** bytes; LCP where it matters
- **moves** `oxipng`, `svgo`, modern formats, size to the display
- **guard** a byte budget per asset in CI

### video / audio / font
- **gates** same duration and streams; every glyph the site uses kept
- **moves** sensible quality settings (lossy needs a yes); font subsetting
- **guard** a byte budget, or none — say so

### spreadsheet
- **gates** every output cell identical
- **measure** recalculation time; used range; volatile function count
- **moves** replace volatile functions; trim the used range
- **guard** none automatable — say so

---

## G. Process and machine

### workflow — runbooks, process docs
- **goal** shorter lead time
- **gates** every output still produced
- **measure** steps, handoffs, wait time
- **moves** cut handoffs and waiting; automate only when the time saved exceeds the cost to build and maintain it
- **guard** standard work (a template); no automated guard — say so

### dev machine
- **goal** faster login, disk back
- **gates** only reversible toggles; nothing the user started is stopped
- **measure** login item count; free space
- **moves** disable unneeded login items; clear rebuildable caches. The
  machine is outside the project, so every change is shown first and applied on yes
- **guard** none automatable — say so
