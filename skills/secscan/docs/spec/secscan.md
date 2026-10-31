# secscan — the security engines and the calls to the best tools, and keyscan, the secret gate
Status: approved 2026-10-23

## 4.1 Feature Overview

Feature: secscan (skill) + keyscan (script)

**One-Line Summary**: `/secscan` (also "security scan") runs every security
engine over the repo, verifies their results, checks secrets first, then calls
the best outside tools for the rest, both on a default run — `claude-security`
for the verified code review and patches, `security-audit` for its domain guides
in depth (revised 24–25 Oct 26). `keyscan` is the fast secret scanner behind it and the commit gate
(today's `secscan` script, upgraded and renamed) — a script, not a command.

**Problem Statement**: security checks are spread over four installed tools
(`/security-review`, Cloudflare's `security-audit`, the `claude-security`
plugin, the `secscan` script) and four engines (gitleaks, trivy, semgrep,
zizmor), each covering part of the ground, overlapping elsewhere, and none
running the others. The owner wants one entry point that runs what no tool
runs (the engines) and calls the others for what they do best — nothing
rebuilt, nothing retired.

**Success Criteria**:
- On a seeded fixture repo, `/secscan` reports each of the 8 seeded flaws,
  each once (no seeded flaw on two lines of the same category within ±3
  lines): a hard-coded key, a vulnerable dependency, a Dockerfile that runs
  as root, a SQL injection, an unpinned GitHub Action, an injected workflow
  expression, a prompt-injection line in a SKILL.md, and a missing ownership
  check only a code review can find — `claude-security`'s "Scan codebase" on
  the seeded mirror (the mirror masks the seeded key, so no gate stands in its
  way).
- On its clean twin, it reports zero findings, every applicable engine `ran`.
- The seeded key's value appears nowhere in the session transcript of the
  run — chat, tool results, verifier outputs, `--report` files.
- `keyscan -s` keeps the commit gate under 0.2 s (median of 5) on a one-line
  staged change, and passes the moved keyscan suite (the old suite minus its
  `--deps`/trivy cases, plus the new ones).
- `claude-security` and `security-audit` stay installed and are called by
  secscan; `code-audit`'s security lens hands off to secscan.

## 4.2 Service Stories (no UI — replaces User Stories)

```
When the owner runs /secscan (or says "security scan") in a project
The system runs every engine that applies to the repo, merges and verifies
their findings, and calls claude-security on a masked copy for the flaws
engines miss
Resulting in one report in chat: findings by severity, each with evidence,
tags and a fix, plus what was covered and what was not
Within ~10 min on a 1k-file repo (engines < 2 min; review scales with the code) — measured 24 Oct 26: engines 6–7 s on the seeded fixture, 55.5 s on `~/.agents` (738 files)

When the owner runs /secscan changes
The same, narrowed to what changed since the last push (~2 min for a typical change set; engines ~7 s on a one-commit fixture change, 24 Oct 26)

Failure mode:
When an engine is missing, blocked by the sandbox, refused or fails
The system reports it as a coverage gap (never a pass) with the command that
fixes it, and the rest of the scan goes on
```

```
When a commit is about to be made (the commit gate)
keyscan -s scans the staged lines with its own patterns and gitleaks' rules
Resulting in ✓ clean (exit 0) or the hits as place + first 4 characters + rules (exit 1)
Within 0.2 s on a small change
```

Acceptance criteria:
- [ ] Given `/secscan` (or "security scan"), then every check runs over the
      whole repo and every top-level folder is listed as covered (by which
      engines) or skipped with a reason, and each called tool is named with its
      job, report and counts, or why it did not run.
- [ ] Given `/secscan changes`, then only findings on lines the changes added
      or modified are reported; the rest are counted as "predates the change".
- [ ] Given an engine not installed, then the report names it under "not
      covered" with its install command, and the run is not "clean".
- [ ] Given a finding, then it carries a place, evidence, severity,
      confidence, tags (CWE, OWASP Top 10:2025, and LLM / Agentic ids where
      they apply) and a fix — never a secret value.
- [ ] Given "fix 2, 5", then secscan hands those findings to `/rev` (which owns
      the failing-test-first fix) and afterwards re-runs the engine or verifier
      that found each one on the patched tree (close-check).

## 4.3 Functional Requirements

FR1: keyscan — the renamed secret scanner
- **Priority**: Critical
- **Input**: `keyscan [path…] | -a | -s | -H [--range BASE..HEAD] | - |
  --mask FILE | --strict | --no-engines | --json`
- **Processing**: the reviewed upgrade staged at
  `/private/tmp/claude-501/-Volumes-NVMe2TB-shrix-Dev-Code-Git-xcratch/c9fb3633-b1a7-48a7-9795-b96254e0f2a1/scratchpad/secscan-work/new/secscan`
  (gitleaks merge, rule labels, allow markers, example keys, `.gitleaksignore`,
  engine failure = hit, sandbox-safe), **minus** `--deps` and the trivy secret
  pass (gitleaks owns secrets). New:
  - `--range BASE..HEAD` (with `-H`): only the commits in that range (own
    `git log BASE..HEAD`, gitleaks `--log-opts BASE..HEAD`) — for changes mode.
  - `--mask FILE`: prints FILE with every own-pattern match, every whole
    `-----BEGIN … PRIVATE KEY-----` … `END` block, and every gitleaks span
    (every line `StartLine`–`EndLine`, whole — columns are not trusted across
    encodings) replaced by `‹redacted:<rule>›` — how the
    review reads a file that holds a secret. It honours no allow marker and no
    `.gitleaksignore`, and fails closed: if gitleaks is installed but cannot
    run, it prints nothing and exits 1; with gitleaks absent or
    `--no-engines` it masks own patterns only and says so on stderr.
  - `--strict`: ignore every allow marker and `.gitleaksignore` — the run
    `scan.py mirror` uses to decide which files it copies masked.
  - `--json`: one object per hit `{place, commit, file, line, preview, rules}`
    (`commit` null when none, `preview` the 4 characters or ""); a note-hit
    (secret-named file, could not scan, engine could not run) is
    `{note, place, reason}`; then `{summary: {hits, places, scanned, skipped,
    exit}}`. The ✓/✗ status line goes to stderr in this mode.
- **Output**: unchanged text form; exit 0 clean · 1 hit or could not
  read/run · 2 could not run at all.
- **Constraints**: the first pattern list stays a verbatim copy of
  `~/.claude/hooks/secret-patterns.sh`; `secscan:allow`, `keyscan:allow` and
  `gitleaks:allow` each skip a line (except under `--strict` and `--mask`); no
  value is ever printed; every `secscan` in the body, rule labels (the
  unnamed-hit label becomes `keyscan`) and test messages is renamed.

FR2: rename sweep
- **Priority**: Critical
- **Processing**, in this order, so the gate is never without a scanner:
  1. `~/.agents/bin/keyscan` created beside `~/.agents/bin/secscan` (the real
     file; `~/.local/bin/secscan` is a symlink to it), and the symlink
     `~/.local/bin/keyscan → ~/.agents/bin/keyscan`.
  2. First of the switches: the ask rule
     `Edit(//Users/shrix/.agents/bin/keyscan)` added in
     `~/.claude/settings.json` beside the `secscan` one — no other reference
     moves before keyscan is guarded; a no here stops the task.
  3. Every reference switched: `~/.claude/rules/git-safety.md` and
     `~/.claude/rules-ref/commits.md` (`secscan -s` → `keyscan -s`);
     `~/.claude/hooks/commit-memory.sh` and its README;
     `~/.claude/security-README.md` and `~/.claude/settings-README.md` (the
     scripts hooks run); the tests (`~/.agents/tests/bin/test_secscan.sh` →
     `test_keyscan.sh`, `test_secret_patterns.sh`'s `SECSCAN_BIN` →
     `KEYSCAN_BIN` and its messages).
  4. `runctl unregister secscan` in a terminal tab (deletes the tracked
     `~/.claude/commands/secscan.md`, trashes `skills/runctl/scripts/secscan`;
     frees the name for the skill; keyscan gets no command — `/secscan
     secrets` is its entry point).
  5. Last: `git rm bin/secscan` in `~/.agents`, the `~/.local/bin/secscan`
     symlink removed, and the `secscan` ask rule removed.
- **Constraints**: settings, rules and hooks are the guard layer — each write
  needs its own in-chat yes; rule edits follow
  `~/.claude/rules-ref/rules-maintenance.md`. A declined yes stops the task
  before step 5: `secscan` stays installed until every reference has moved.
  The sweep afterwards finds no reference to the old script, except: the
  `secscan:allow` marker, the new skill, and
  `~/.agents/skills/picsynth/docs/plan/picsynth-music-google.md:29` (another
  session's file — left and recorded in `docs/tasks.md`).

FR3: scan.py — the engine runner
- **Priority**: Critical
- **Input**: `scan.py [full|changes|deps|secrets|code|ci|agents] [--base SHA]
  [--only ENGINE] [--json] [path]` (default `full`); `scan.py
  doctor`; `scan.py update`; `scan.py report FINDINGS.json OUTDIR`. The skill
  runs it in a Terminal-panel tab when one exists (spike S1: semgrep,
  skillspector and trivy misconfig cannot run inside Claude's sandbox);
  through Bash those three report `blocked` with the terminal command.
  skillspector runs with every proxy set to a closed local port, so its
  OSV.dev lookup fails at once and no dependency name leaves the machine. Its
  SC4 results (known-vulnerable dependencies) are dropped where trivy ran
  over a file it reads (an exact `requirements.txt` and lockfiles), since
  trivy's local database is fuller (26 Oct 26: 18 flaws in two packages
  against SC4's 2); for files trivy does not read (other requirements files,
  `setup.py`, and a `package.json`, `pyproject.toml` or `Pipfile` with no
  lockfile beside it), SC4's built-in list is kept and the coverage line
  names the file.
- **Processing**: decides which engines apply (§ 4.6), runs each with its
  safe flags under a per-engine timeout, parses its output, maps every result
  to one Finding (§ 4.4) with a category, merges duplicates per root cause
  (same file, category, package and commit; a member's own line always joins;
  within 3 lines of the cluster's first line, another engine with a compatible
  CWE or the same engine with the same CWE; a secret only on the same line),
  lists repo suppressions it could not switch off
  (§ 4.9.1), and records coverage per engine and per top-level folder.
  Changes mode: base = `@{push}`, else `origin/<branch>`, else the merge-base
  with the default branch, else it says so and runs full; engines scan the
  changed files, and findings on lines `git diff -U0 <base>` did not add or
  modify are counted as "predates the change".
- **Output**: findings + coverage + suppressions, text (default) or JSON;
  `report` renders the final findings (engine + review) to
  `OUTDIR/secscan-<YYYY-MM-DD>.md` and `.json` (`-HHMMSS` added on a same-day
  rerun).
- **Constraints**: stdlib Python 3.9+; a missing, blocked, refused, failed or
  data-less engine is a coverage gap, never a pass; trivy 0.69.4–0.69.6
  refused; engines scan offline and without telemetry; no value is printed
  (keyscan previews only; other engines' snippets are replaced by the place).

FR4: engine data refresh
- **Priority**: High
- **Input**: `scan.py update`
- **Processing**: downloads trivy's vulnerability DB, Java DB and misconfig
  checks bundle, and semgrep's registry packs (`p/default` and the language
  packs, via `https://semgrep.dev/c/p/<pack>`) into
  `${SECSCAN_CACHE:-${XDG_CACHE_HOME:-$HOME/Library/Caches}/secscan}` (~3 GB;
  on this machine a symlink to the NVMe), with a
  `stamp.json` of dates; the packs stay there — the Semgrep Rules License
  forbids redistributing them, and they never enter the skill.
- **Constraints**: the only step that uses the network; inside the sandbox it
  prints the exact terminal command instead. Scans warn when data is older
  than 7 days, and report `no-data` coverage when it is missing.

FR5: the review — called, not rebuilt (revised 24 Oct 26)
- **Priority**: Critical
- **Processing**: secscan does not review code itself. It invokes
  `claude-security` for the code review — threat model, parallel researchers,
  its own verifier panel and report; effort low / medium / high from the profile
  quick / standard / deep: "Scan codebase" with the masked mirror as its
  `[path]` (bare, `code`, and in `changes` scoped to the folders of every
  changed file, committed and uncommitted), and "Scan changes" `--base <the
  scan's base>` for the committed range when the secrets gate is open.
  It invokes the `security-audit` skill on the mirror in its full-audit mode on
  every default run (bare, `code`, `changes`; not `quick`) for its domain guides
  in depth, alone for `audit`, and for `agents` (its AI, LLM and agent guide).
  A per-lens check (25 Oct 26) found the removed own review covered only by
  the two tools together. Every `security-audit` call also asks for API
  footguns, ASVS 5.0 ids where a control is named, and the project's
  precedents honoured at their exact place; `claude-security`'s workflow takes
  no free text, so secscan applies the precedents (file, line and CWE id must
  match) and adds the ASVS ids to its findings itself, and moves its report out
  of the mirror before `security-audit` reads it (26 Oct 26). It verifies only its own engines' results: fresh
  isolated verifiers through the mirror, one lens (is the match real;
  reachability and defences set the severity, never the verdict), a panel of
  three for each high/critical result and each group, one verifier for the
  rest; votes per `references/verify.md`. Where subagents cannot be dispatched,
  verification runs inline, labelled `self-verified — isolation unavailable`.
- **Constraints**: **every reader gets the mirror** — the called tools read the
  masked copy, never the repo, and each call is told to read only under that
  path; a failed mirror means no hand-off. The calls that read the live
  checkout ("Scan changes", "Suggest patches" — neither takes a path) run only
  behind **the secrets gate**: `keyscan -a --strict` over every file, gitignored
  ones included, and a `secrets` run over all history, whatever the mode, both
  `ran`, no hit, no secret-named file, and every history hit one the owner has
  said is revoked; otherwise the call is skipped and named under not covered,
  and `changes` mode reviews the changed folders through the mirror instead
  (revised 24 Oct 26 after review). A called
  tool's findings are reported as that tool's, never re-scored; a tool not
  installed, not run or stopped is a coverage gap. **Secrets in secscan's own
  reads**:
  - the engine verifiers read only the masked mirror (`scan.py mirror DEST
    [PATH]`), never the repository: a file with any `keyscan --strict` hit is
    copied through `keyscan --mask`; secret-named, binary, oversized, symlinked,
    unvouched and control-character-named files are left out; the copy is
    scanned again and a file still matching is removed; the mirror is deleted
    when the run ends;
  - a secret-named file (`.env*`, `*.pem`, `*.key`, `secrets.ya?ml`,
    `credentials.*`, `id_rsa`, …) is never read by any means — its name is
    the finding;
  - a history hit's commit and file are never shown;
  - verifier briefs, and code-audit's lens-4 subagent, carry these rules and
    never quote a flagged line; evidence quotes code, never a value.

FR6: report
- **Priority**: Critical
- **Output**: in chat — summary line; one findings table by severity (# ·
  severity · place · title · confidence · tags); each finding's evidence and
  fix below it; "needs validation"; hardening notes; suppressions honoured;
  coverage (engines, top-level folders, what was not covered and why); the
  revision (`sha12`, `-dirty`); engine versions. `--report` also writes it
  via `scan.py report` to `docs/security/` in the scanned project. Zero
  findings is a result, stated with its coverage.
- **Constraints**: tags from engines where they give them, else from the
  CWE → OWASP Top 10:2025 table in `references/report.md`; OWASP LLM / Agentic
  ids for AI and agent findings. A called tool's findings keep that tool's own
  tags and verdicts. No secret value anywhere.

FR7: fixes, on request only
- **Priority**: High
- **Input**: the owner names findings ("fix 2, 5")
- **Processing**: a leaked key → the owner revokes it at the provider first,
  then `/rev` removes it; a code flaw → secscan prepends an audit entry to the
  project's `docs/logs/revlogs.md` in `code-audit`'s entry format (IDs `A1`…,
  each with place, root cause and the smallest fix at the last trusted
  decision point, base = the scanned revision) and runs `/rev A<n> …`, which
  reads those IDs from the newest audit entry (`rev/SKILL.md` § Audit
  findings by ID) and owns the failing-test-first fix; afterwards
  secscan re-runs `scan.py <mode> --only <engine>` on the patched tree — the
  close-check (a `claude-security` finding is closed by that tool's re-scan, its
  fixes are its "Suggest patches" job); a false
  positive → `keyscan:allow`, `.gitleaksignore` or a precedents entry, on the
  owner's word.
- **Constraints**: never fixes unasked; tests that run target code run only
  inside `/rev`, in the owner's own project, on the owner's request.

FR8: keep the better tools, call them (revised 24 Oct 26)
- **Priority**: Medium
- **Processing**: nothing is retired — Cloudflare `security-audit` and the
  `claude-security` plugin stay installed and enabled; secscan calls them (FR5).
  `code-audit`'s lens 4 runs `scan.py full --json` and verifies the engine
  results per `references/verify.md` inside its subagent (verification inline,
  labelled), with FR5's secret-reading rules in its brief, and names
  `/claude-security` "Scan codebase" (and `security-audit` for depth) in its Next
  steps, since `claude-security` cannot run inside a subagent;
  `~/.agents/skills/CONVENTIONS.md` records secscan's boundary and hand-offs.
- **Constraints**: `/security-review` is built into Claude Code and stays.

FR9: engines installed
- **Priority**: High
- **Processing**: `brew install actionlint hadolint gosec` (Phase 0);
  skillspector is installed as a uv tool and runs only outside Claude's
  sandbox, with its OSV.dev lookup cut off (S6).

## 4.4 Data Model

```
Finding {
  id: string,              // 12 hex: sha256(category, file, commit, line (or package), first rule);
                           // a merged finding takes the id of its highest-severity member
  sources: list[string],   // keyscan, trivy, semgrep, zizmor, actionlint, skillspector,
                           // hadolint, gosec, review
  rules: list[string],     // the engines' rule ids
  category: enum,          // secret | dependency | misconfig | injection | access | crypto |
                           // ci-pin | ci-injection | prompt-injection | memory | logic | other
  severity: enum,          // critical | high | medium | low | info (per-engine map, § 4.6)
  confidence: enum,        // high | medium | low (engines: their own field, else high; review: from votes)
  verdict: enum,           // candidate | confirmed | needs_validation | rejected
  file: string, line: int|null, commit: string|null,
  title: string, evidence: string,          // never a secret value
  tags: list[string],      // "CWE-89", "OWASP:A05", "LLM01", "ASI01"
  fix: string|null
}                          // changes mode drops predating hits; the document counts them (predates_change: int)
Coverage { engine: string,
           state: ran | n/a | missing | blocked | refused | failed | no-data,
           reason: string, scope: string, version: string }
FolderCoverage { folder: string, engines: list[string], skipped_reason: string|null }
Suppression { file: string, line: int, marker: string }   // trivy:ignore, keyscan:allow, secscan:allow, gitleaks:allow on their line; ".semgrepignore:<pattern>" and ".gitleaksignore:<entry>" with that file's line
```

Exit: `n/a` is not a gap; every other non-`ran` state is.
**Storage**: in memory per run. `--report` writes `docs/security/` in the
scanned project (places and 4-character previews only — safe to commit; the
report says so). Project precedents: `docs/security/precedents.md`
(committed, the owner's triage decisions; read in the mirror). Engine data:
`${SECSCAN_CACHE:-${XDG_CACHE_HOME:-$HOME/Library/Caches}/secscan}/` — trivy's
databases, the semgrep packs and their merged `semgrep/rules.yml`, `stamp.json`.

## 4.5 Service Interface (no UI — replaces UI/UX)

**Trigger**: `/secscan [changes|deps|secrets|code|ci|agents] [quick|deep]
[--report] [path]` — bare `/secscan` is every check over the whole repo;
trigger phrases "security scan", "security audit", "secscan", "is this
secure", "audit this for security", "scan for secrets", "any keys in here",
"check before I push". It is the only security entry point: `keyscan` has no
command of its own (`/secscan secrets` runs it).
**Input contract**: a folder; changes mode needs a git repo with a base.
**Output contract**: § FR6. **Side effects**: none, except `--report` files,
precedents entries the owner asked for, and — on "fix …" — an audit entry
prepended to `docs/logs/revlogs.md` and the fixes `/rev` makes.
**Observability**: the report's coverage section; `scan.py doctor` lists
engines, versions, data age and sandbox blocks.

## 4.6 Technical Architecture

```
~/.agents/skills/secscan/
├── SKILL.md                 modes, secrets gate, the calls to claude-security and security-audit
├── scripts/scan.py          engine runner + report renderer
├── references/
│   ├── false-positives.md   dismissal tests and precedents for engine results
│   ├── verify.md            the engine-result verifier brief (incl. the masked-read rule)
│   ├── report.md            layout, severity anchors, CWE → OWASP 2025 table
│   ├── fixes.md             patches via claude-security, engine fixes via /rev, the close-check
│   └── NOTICE.md            MIT notices (Cloudflare, Anthropic); MITRE CWE notice
└── docs/                    spec, plan, reqs, arch, tasks, research
~/.agents/bin/keyscan        secret scanner + commit gate (tracked; linked from ~/.local/bin)
~/.agents/tests/bin/test_keyscan.sh
~/.agents/tests/skills/secscan/   scan.py tests, fake engines, make_fixture.py
```

| need | engine | runs when | flags (S1–S8 confirm) | severity map |
|---|---|---|---|---|
| secrets | keyscan | always | `--json`; full: paths + `-H`; changes: changed files, `-s`, `-H --range <base>..HEAD` | high |
| deps, misconfig, licences | trivy | full, deps; changes when a manifest, lockfile, Dockerfile or IaC file changed | `fs --scanners vuln,misconfig,license --format json --cache-dir <cache>/trivy --skip-db-update --skip-java-db-update --skip-check-update --offline-scan --disable-telemetry --skip-version-check --ignorefile <empty>`; CVEs grouped one finding per package | trivy's own |
| code | semgrep | full, code; changes on any changed file | `scan --json --metrics off --disable-nosem --config <cache>/semgrep/rules.yml` (the packs merged; each pack when unmerged); `HOME` set to a temp folder | ERROR high · WARNING medium · INFO info |
| CI security | zizmor | `.github/workflows` exists | `--offline --no-config --no-ignores --format json` | zizmor's own; informational → info |
| CI correctness | actionlint | `.github/workflows` exists | `-format '{{json .}}' -config-file <empty>` | medium |
| agent skills / MCP | skillspector | a `SKILL.md`, `.claude/` or `.mcp.json` exists | `scan --no-llm --format json --output <tmp>` (outside the sandbox), every proxy set to `http://127.0.0.1:9` and `NO_PROXY` empty, so its OSV.dev lookup fails at once; its SC4 results are dropped where trivy ran over a file it reads | its own |
| agent dependencies | trivy | agents mode: an agent folder holds a dependency file trivy reads (`requirements.txt`, a lockfile) | one `fs --scanners vuln` run over the scope, offline as above; only results inside those agent folders are kept | trivy's own |
| Dockerfiles | hadolint | a `Dockerfile*` exists | `-f json --disable-ignore-pragma` (S5) | error high · warning medium · info/style low |
| Go | gosec | `go.mod` exists | one run per `go.mod` folder, from that folder: `-fmt json -quiet -nosec ./...`, `GOFLAGS=-mod=readonly GOPROXY=off GOTOOLCHAIN=local` | gosec's own |

trivy, semgrep, zizmor, hadolint and skillspector run with an empty temp folder
as cwd on absolute paths; keyscan and actionlint run from the repo top (git and
`-config-file <empty>` keep their config explicit), gosec from each module root
(its repo config cannot silence it). Every engine gets an empty HOME except
gosec, which reads Go's module cache.

**Data flow**: `SKILL.md` → `scan.py <mode>` (engines → findings, coverage,
suppressions) → `scan.py mirror` (masked copy of the whole repo) → engine-result
verifiers on the mirror → `claude-security` "Scan codebase" and `security-audit`
on the mirror, one after the other (one alone for `quick`, `agents`, `audit`); "Scan changes" on the repo only behind the
secrets gate → report (`scan.py report` when `--report`) → fixes on request
(`claude-security` patch files; engine findings via `/rev`) → close-check.

## 4.7 API Contracts (CLI)

```
keyscan --json …     → per hit: {"place":"a.py:3","commit":null,"file":"a.py","line":3,"preview":"AKIA","rules":["aws-access-token"]}
                       per note: {"note":"could not scan","place":"locked.md","reason":"Permission denied"}
                       last:     {"summary":{"hits":1,"places":1,"scanned":"12 files","skipped":0,"exit":1}}
keyscan --mask FILE  → FILE's text, each match replaced by ‹redacted:<rule>›; exit 0 (1 if FILE unreadable)
scan.py <mode> --json → {"revision":"<sha12>[-dirty]","mode":"…","base":"…|null","note":"…","predates_change":0,
                         "findings":[Finding…],"groups":[{"engine","rule","unit","count","severity","title",
                         "ids":[…],"members":[n…]}…],"coverage":[Coverage…],"folders":[FolderCoverage…],
                         "suppressions":[Suppression…],"data_age_days":{"trivy":2,"semgrep":2},
                         "versions":{"trivy":"0.76.1",…}}
                       stderr while it runs: "▸ <engine> <state> at <s> s[, <n> raw hit(s)][ — revoke first: <places>]"
scan.py exit: 0 ran, nothing found, no gap · 1 findings or a gap · 2 could not run
scan.py mirror DEST [PATH] → DEST/<repo paths> masked copies + DEST/.secscan-mirror.json
                         {"masked":["config.py"],"skipped":[{"file":".env","why":"secret-named"}]} (names masked);
                         exit 2 (nothing left behind) when keyscan cannot scan or re-check, DEST is inside the repo or not empty
scan.py report JSON OUTDIR → the scan JSON with the verifiers' verdicts, plus profile, needs_validation,
                         hardening, rejected [{"place","reason"}], tools [{"tool","job","report","summary"}] (references/report.md)
settings: SECSCAN_JOBS (workers, default the CPU count) · SECSCAN_TIMEOUT (s per engine run, 600) ·
          SECSCAN_PASS_ENV (extra env-name prefixes engines may see) · SECSCAN_CACHE · SECSCAN_<ENGINE> (binary)
```

`scan.py` runs every applicable engine at once: version checks in parallel, then
every run of every engine (one per skill folder for skillspector, one per Go
module for gosec) in one thread pool, keyscan's queued first; coverage keeps the
mode's engine order, and an interrupt kills every engine's process group.

## 4.8 Edge Cases & Errors

| Error | Cause | Message | Recovery |
|---|---|---|---|
| engine missing | not installed | `trivy: missing — not installed — brew install trivy` | gap; scan goes on |
| engine blocked | sandbox (CA path, network, HOME writes) | `semgrep: blocked — blocked by the sandbox — run in a terminal: <command>` | gap + the exact command |
| engine failed | non-zero exit, unparseable output, a result it could not map | `semgrep: failed — <first error line>` | gap |
| engine timed out | hang | `gosec: failed — timed out after 600 s` (provisional) | process group killed; gap |
| known-bad version | trivy 0.69.4–0.69.6, read from its install without running it | `trivy 0.69.4 is a compromised release — upgrade it` | refused, never run; gap |
| unreadable version | trivy whose install path and Go build info give no release | `trivy's version cannot be read without running it … install it with Homebrew` | refused, never run; gap |
| bad setting | `SECSCAN_JOBS` or `SECSCAN_TIMEOUT` not a whole number | `✗ could not scan: SECSCAN_JOBS must be a whole number …` | exit 2 |
| mirror failed | keyscan cannot scan or re-check, DEST unsafe | `✗ could not scan: …` | exit 2; no review, reported under not covered |
| stale data | > 7 days | text mode: `trivy data 9 days old — run scan.py update`; `--json`: `data_age_days`, which the skill reads and tells the owner | warns |
| no data | never updated | `semgrep: no-data — no rule packs cached — run scan.py update` | gap |
| no base | changes mode, no upstream, no origin, no default branch | `changes mode needs a push target — running full` | full |
| not a git repo | changes mode | `changes mode needs git — running full without history` | full |
| nothing changed | changes mode, all pushed | most engines `n/a — no … changed`; keyscan still checks the staged set and the range | runs; ci or agents mode exits 1 ("no engine ran") |
| huge repo | > 20k files | `claude-security` asks its own size question; secscan's engines run whole | the tool's default |
| secrets gate shut | a tree hit, an unrevoked history hit, or keyscan not `ran` | `not covered: claude-security Scan changes — <why>` | the owner revokes and removes; offered again |
| mirror failed | keyscan cannot scan or re-check | `not covered: verification and hand-offs — <why>` | nothing reads the repo instead |
| repo suppressions | markers in the repo: `trivy:ignore` and `.semgrepignore` patterns (no flag switches them off), `keyscan:allow`, `secscan:allow`, `gitleaks:allow` and `.gitleaksignore` entries (keyscan honours them outside `--strict`) | each listed with file and line | listed in the report |
| secret in a snippet | an engine echoes code | replaced by the place | never printed |
| injection text in the repo | a file instructs an agent | skillspector finding in agent folders; elsewhere a verifier reports it as a `prompt-injection` lead | never followed |
| nested run | secscan inside a subagent (code-audit) | `self-verified — isolation unavailable` | inline verification |

## 4.9 Non-Functional Requirements

Performance: `keyscan -s` < 0.2 s on a small change (median 0.103 s at Task 2,
0.08 s in the /rev check);
engines < 2 min and the full run ~10 min on a 1k-file repo. Measured 24 Oct 26
(A1): the seeded fixture's engines 6.1–7.3 s in all (semgrep ~6 s of it), the
clean twin 5.8–6.4 s; `~/.agents` 738 files 55.5 s with engines in parallel
(116.5 s one after another), its floor skillspector on archify (46 s). The
review and verifiers are not timed.
Security: no secret value in the transcript (keyscan previews; gitleaks
`--redact`; snippets replaced; secscan's verifiers and the called tools read
only the masked mirror, "Scan changes" only behind the secrets gate); engines
offline and telemetry-free during scans; known-bad versions refused; repo
content is data; read-only unless the owner asks for a fix (done by `/rev`).
Threat model: § 4.9.1.
Accessibility: N/A — text output in a terminal or chat; no UI.
Scalability: engines in parallel with timeouts; a verifier panel only for
high/critical results and groups; `claude-security` sizes its own review.
Compatibility: macOS; bash 3.2 for keyscan; Python 3.9+ stdlib for scan.py.
Licences: no copied text from the claude-security plugin (proprietary) or
Trail of Bits / OWASP (CC BY-SA — re-expressed); MIT text from Cloudflare and
Anthropic only with their notices; semgrep rules never bundled.

### 4.9.1 Threat model (inline companion)

| asset | threat | control | residual risk |
|---|---|---|---|
| secrets keyscan's patterns or gitleaks' rules match | printed into chat, tool results, verifier output, a called tool's report | engines print places + 4-char previews; snippets replaced; secscan's verifiers, `claude-security` "Scan codebase" and `security-audit` read only the masked mirror; "Scan changes" and "Suggest patches", which need the repo, run only behind the secrets gate (whole tree + all history clean, history hits revoked) (files with a `--strict` hit copied via `keyscan --mask`, which fails closed and masks PEM blocks; the copy re-scanned); secret-named files never copied or read; history hits never shown; A3 greps the session's whole folder (subagents, tool results) | a rule-matched value inside a file read before scan.py ran — the skill runs scan.py first |
| secrets no rule matches | a called tool reads them in plain text | none beyond the rules | a value in an unknown format can reach the transcript; stated in every report's coverage |
| the owner's machine | a scanned repo's code runs | engines are static; secscan runs no target code; fixes and their tests run only in `/rev` on the owner's request; `security-audit` may build the target in its own sandbox, said to the owner first | build-time hooks run inside `/rev` or `security-audit`'s sandbox |
| the verifiers' judgement | prompt injection in repo text | repo text is data; injection attempts become findings; verifier briefs carry the engine's words and places, not the repo's text | a subtle injection may still bias a verdict; the panel's 2-of-3 limits it |
| engine integrity | a compromised release (trivy 2026) | known-bad version list, read from the install (Homebrew path, Go build info) so a bad build never runs; an unreadable version refused; engines see only an allowlisted environment, never credentials; versions in every report | a not-yet-known bad release |
| a hostile repo's links | a symlink reads a file outside the repo into the output | any path with a symlink on it is never read by scan.py or named to an engine; the mirror lists them as skipped | engines given the whole folder (trivy, semgrep, keyscan) follow their own symlink rules |
| scan config | the repo silences its own scan | empty cwd (keyscan, actionlint and gosec as § 4.6) + explicit config; `--no-config --no-ignores`, `--disable-nosem`, `-nosec`, `--ignorefile ""`, `--disable-ignore-pragma`; every repo marker (`trivy:ignore`, `.semgrepignore`, allow markers, `.gitleaksignore`) is listed as a suppression | listed, not hidden |
| data leaving the machine | telemetry, registry lookups, module downloads | offline flags; gosec `GOPROXY=off`; skillspector, which has no offline switch (S6), runs with every proxy set to a closed local port (checked 26 Oct 26: its OSV.dev request reached only a local listener); network only in `scan.py update` | a skillspector release that opens a connection without honouring the proxy variables |

## 4.10 Testing Strategy

**Levels**: unit — scan.py planning, each parser (recorded engine output),
merge, categories, coverage states, version refusal, snippet replacement,
changes-mode line filter; keyscan's suite moved to `test_keyscan.sh` with
`--range`, `--mask` and `--json` cases; integration — scan.py against fake
engines and against the real engines on the seeded fixture; manual — one
`/secscan` run on a real project.
**Hard to test**: the code review — `claude-security` on the seeded mirror must
find the one flaw only a review can (the ownership check), and on the clean
twin nothing; the sandbox — spike S1 runs each
engine inside and outside it; the transcript — A3 greps the session's
`.jsonl` for the seeded value.
**Acceptance**: each success criterion in § 4.1 is its own plan task.

## 4.11 Implementation Roadmap

Roadmap: see docs/plan/secscan.md

## 4.12 Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| engines blocked in Claude's sandbox | High | High | S1 first; blocked = gap + command; `update` outside |
| semgrep packs need network and metrics | Med | Med | S2: cached packs, `--metrics off`, `HOME` in temp |
| review reads an unmatched secret | Med | Med | stated residual risk; keyscan + gitleaks cover the known formats |
| review cost on a large repo | Med | Med | profiles; panel for High/Critical only in standard |
| rename leaves the gate without a scanner | Low | High | FR2's order: install beside, switch, remove last; a declined yes stops before removal |
| gitleaks is security-patch-only | Certain | Low | pinned; Betterleaks swap in tasks |
| licence slip | Low | Med | Task 7's phrase check against the sources |

**Rollback Plan**:
1. keyscan: `git revert` the rename commits in `~/.agents` (restores
   `bin/secscan`) and `~/.claude` (rules, hooks); restore the
   `~/.local/bin/secscan` symlink and the settings ask rule; `runctl register
   ~/.local/bin/secscan` with the old description.
2. secscan skill: remove its `~/.claude/skills/secscan` symlink.
3. Retired tools: re-clone Cloudflare's skill; re-enable the plugin.

**Kill switch**: `keyscan --no-engines` (own patterns only) or `/secscan secrets`.

### 4.12.1 Spikes (ordered first in the plan; results in `secscan-spikes.md` — S1 and S6 partial, the rest pass)

| # | assumption | check | on a fail |
|---|---|---|---|
| S1 | each engine runs inside Claude's Bash sandbox | each once inside and once in a terminal tab on the fixture | that engine is `blocked` by design: gap + command |
| S2 | semgrep scans from cached packs, offline, `--metrics off`, `HOME` in temp | cache packs via `update`; scan inside the sandbox | semgrep runs outside the sandbox only |
| S3 | trivy reads DB, Java DB and checks bundle offline | after `update`, vuln + misconfig scan inside | trivy deps runs outside only |
| S4 | gitleaks `--config` (extend default) keeps every default rule in git mode | hits with and without | drop `--config` in git mode; list `.gitleaks.toml` as a suppression |
| S5 | each engine's inline-suppression switch exists in the installed version | `--help` + a fixture with each marker | marker listed as a suppression |
| S6 | skillspector runs offline (e.g. `SSL_CERT_FILE=/etc/ssl/cert.pem`, no network → bundled fallback) | inside the sandbox, network off | runs only on the owner's allow, else `blocked` |
| S7 | gosec runs offline from the module root | `GOPROXY=off` on the fixture's `go.mod` | gosec `blocked` when modules are missing |
| S8 | a subagent can (or cannot) dispatch its own subagents | try from a subagent | confirms the inline-verification fallback |

## 4.13 Out of Scope

- DAST (ZAP, nuclei): needs a running target. Future: No.
- Container image scanning: no images here. Future: Yes (trivy image).
- SARIF output: no consumer yet. Future: Yes.
- Live secret verification (sends keys to providers): unsafe. Future: No.
- osv-scanner reachability, guarddog: deep-mode extras. Future: Yes.
- Betterleaks in place of gitleaks: wait for v2 stable. Future: Yes.
- CI integration (GitHub Action): local tool first. Future: Yes.
- Masking secrets no rule matches: no reliable detector. Future: No.

---

## Decided
- secscan does only what no outside tool does — the engines, their merged and
  verified results, the secrets gate — and calls `claude-security` (code review,
  patch files) and `security-audit` (domain guides in depth) for the rest — both
  on a default run (owner, 25 Oct 26); neither is
  retired; the best quality wins over convenience at every point (owner,
  24 Oct 26). This supersedes the "single security check" and the retirements
  below.
- keyscan = the secret scanner and commit gate, renamed from `secscan`, with the
  reviewed engine merge, minus `--deps` and trivy's secret pass (owner, 23 Oct).
- `secscan` = a new shrix skill, the single security check, blending the
  methods and engines in `docs/research/security-landscape.md` (owner, 23 Oct).
- One security entry point: `/secscan`, also "security scan"; bare it runs every
  check over the whole repo; `changes`, `deps`, `secrets`, `code`, `ci`, `agents`
  narrow it; keyscan gets no command (owner, 23 Oct, mid-spec).
- `secscan:allow` keeps working; `keyscan:allow` added (owner, reco 1).
- Report in chat; `--report` writes `docs/security/`; fixes offered, applied only
  on request (owner, recos 4–5).
- Engines: keyscan (gitleaks), trivy, semgrep, zizmor, actionlint, skillspector
  `--no-llm`, hadolint, gosec (owner, 23 Oct).
- Retire Cloudflare `security-audit` and the `claude-security` plugin after the
  blend, each on its own yes; `/security-review` stays (owner).
- `code-audit` lens 4 hands off to secscan (owner, reco 6).
- Order: /spec → /dev → /rev (owner).
- Success is measured by the § 4.1 criteria on a seeded fixture (8 flaws, one
  only review can find) and its clean twin (owner's go, 23 Oct).

## Assumptions
- Approach A: skill + `scan.py` + references + subagent panel.
- scan.py is stdlib Python; keyscan stays shell and lives at `~/.agents/bin/keyscan`.
- Fixes are `/rev`'s (it owns the failing-test-first gate); secscan briefs and close-checks.
- Profiles: standard by default; deep on request; quick only when the owner says
  so (it drops `security-audit`, so it is never taken by itself on a large repo —
  `claude-security` sizes its own scan there).
- Engine data cache: `${SECSCAN_CACHE:-${XDG_CACHE_HOME:-$HOME/Library/Caches}/secscan}/`.
- Merge per root cause (§ 4.3 FR3's rule); CVEs grouped per package.
- `--report` files hold places and 4-char previews only, so they are safe to commit.
- ADRs: this skill keeps no `docs/adr/`; decisions go to `docs/arch.md` with their why.

## Open questions
None. (Success is measured by the § 4.1 criteria on a seeded fixture and its
clean twin — the recommended answer, taken on the owner's go of 23 Oct; now in Decided.)

## Prerequisites
- The owner's yes per guard-layer write: the settings ask rule
  (`Edit(//Users/shrix/.agents/bin/secscan)` → `keyscan`),
  `~/.claude/rules/git-safety.md`, `~/.claude/rules-ref/commits.md`,
  `~/.claude/hooks/commit-memory.sh` + README, `~/.claude/security-README.md`,
  `~/.claude/settings-README.md`; and per delete (`bin/secscan`, its symlink,
  `test_secscan.sh`, `~/.claude/commands/secscan.md` via `runctl unregister`,
  the old ask rule).
- The owner's yes for secscan depending on `keyscan`, a script outside the skill
  (recorded in CONVENTIONS.md).
- The owner runs, or approves a terminal tab for, `brew install actionlint
  hadolint gosec` and the first `scan.py update` (network).
- Separate yeses at the end: remove Cloudflare `security-audit`; disable
  `claude-security`.

## To file
Filed 23 Oct 26; each file now holds the current entries (superseded in place
by `/spec update`), so the lists below are the record of that first filing.
- **reqs** → `docs/reqs.md`:
  - `/secscan` (also "security scan") is the single security check: bare, every applicable engine and Claude's review over the whole repo; `changes`, `deps`, `secrets`, `code`, `ci`, `agents` narrow it; profiles quick/standard/deep.
  - Engines: keyscan (gitleaks), trivy, semgrep, zizmor, actionlint, skillspector, hadolint, gosec.
  - A missing, blocked, refused, failed or data-less engine is a coverage gap, never a pass, and names its fix.
  - No secret value appears in the transcript: engine previews only, and the review and its verifiers read only the masked mirror (`scan.py mirror`), never the repository.
  - The review never runs the target's code; fixes are offered and, on the owner's word, made by `/rev`, then close-checked.
  - `--report` writes `docs/security/secscan-<date>.{md,json}`; the owner's triage lives in `docs/security/precedents.md`.
  - `keyscan` is the commit gate: own patterns + gitleaks, < 0.2 s on a small staged change, `secscan:allow`/`keyscan:allow`/`gitleaks:allow` honoured; it has no command of its own.
  - Engines scan offline and without telemetry; only `scan.py update` uses the network.
  - Known-bad engine versions (trivy 0.69.4–0.69.6) are refused.
- **arch** → `docs/arch.md`:
  - Engines detect, Claude reviews — why: engines can't find logic flaws, Claude can't match rule databases.
  - One Finding shape, merged on file + category ± 3 lines — why: one root cause, one line.
  - Fresh isolated verifiers, three lenses, 2 of 3; inline and labelled when nested — why: an author grading its own finding confirms it.
  - Engine data in a user cache refreshed by `update` — why: the Semgrep Rules License forbids bundling, and scans stay offline.
  - Engines from an empty folder with explicit config; un-switchable suppressions listed — why: a repo must not silence its own scan unseen.
  - keyscan stays a separate script in `~/.agents/bin`, linked from `~/.local/bin` — why: the commit gate must stay fast and dependency-light.
  - Fixes hand off to `/rev` — why: one owner for the failing-test-first gate.
- **design** → `DESIGN.md`:
  - Report: summary line, one findings table by severity (# · severity · place · title · confidence · tags), details below, then needs-validation, hardening, suppressions, coverage; zero findings stated with coverage.
- **tasks** → `docs/tasks.md`:
  - Build secscan — docs/plan/secscan.md
  - `picsynth-music-google.md:29` still says `secscan -s` — the picsynth session updates it to `keyscan -s`.
  - Later: container image scanning; SARIF output; osv-scanner reachability and guarddog in deep mode; Betterleaks once v2 is stable; a GitHub Action.
- **CONVENTIONS.md** (`~/.agents/skills/`) — filed by plan Task 13, once the skill exists: boundary row `secscan` — owns security checks (engines + review); hands off fixes → `/rev`, docs → `/spec`; bundle rows `| security review | secscan rev |` and `| audit security | code-audit secscan |`; secscan's use of `keyscan` recorded beside the shared scripts.
- **Retirements**: Cloudflare `security-audit` removed; `claude-security` disabled; code-audit lens 4 → secscan.

## Review
Round 1 (isolated, Opus): 3 Critical, 13 Important, 12 Minor — every Critical
and Important fixed in this revision:
- C1 settings ask rule → FR2 step 2, Prerequisites, Task 2 sweep.
- C2 real file is `~/.agents/bin/secscan` → FR2, § 4.6, rollback, Tasks 0–2.
- C3 secrets through the review → FR5 masked reads (`keyscan --mask`), § 4.9.1 narrowed with residual risk, A3 greps the transcript.
- I1 gate order → FR2 order + stop rule. I2 changes-mode commits → `keyscan -H --range`.
- I3 repo suppressions → flags per engine + the suppressions list + S5.
- I4 offline flags → trivy flags, gosec env, S6/S7. I5 empty cwd → gosec exception; no `--baseline-commit` (own line filter).
- I6 installs and fixture → Phase 0. I7 acceptance counts → categories, CVEs per package, one Dockerfile flaw, `go.mod` in the fixture, coverage states split.
- I8 missing tasks → report renderer, precedents, profiles, close-check, folder coverage, predates counts, timings (plan).
- I9 data model → sources/rules lists, category, tags, severity map, states.
- I10 boundaries → fixes to `/rev`; keyscan dependency recorded; nested runs verify inline (S8).
- I11 To file → CONVENTIONS and retirement entries added. I12 → review never runs code; `/rev` does. I13 sweep → `~/.agents/bin`, settings, named exceptions.
- Minors fixed: M1 kill switch, M2 suite wording, M3 triggers, M4 install sources, M5 cache path (S2 decides the download), M6 JSON notes/stderr, M7 parse returns errors (plan), M8 spikes file, M9 accessibility/scalability, M10 base fallback, M11 estimates, M12 report safety.
Round 2 (fresh, isolated): 0 Critical, 8 Important, 4 Minor. C1 and C2
confirmed fixed; engine flags confirmed for gitleaks, trivy, semgrep, zizmor
(hadolint, gosec, actionlint unverified until S5/S7). All 12 fixed — **fixed
after round 2 — not re-reviewed** (beyond /spec's log-only rule for round-2
Importants, because five would have broken the build):
- I-1 masked-read selection from a `--strict` run; secret-named files never read; history hits never shown.
- I-2 `--mask` masks PEM blocks and gitleaks multi-line spans, fails closed.
- I-3 A3 greps the session's whole folder. I-4 lens-4 brief carries the rules.
- I-5 fixes reach `/rev` through an audit entry in `docs/logs/revlogs.md` (rev's existing input).
- I-6 suppressions consistent; zizmor `--no-ignores`; `Suppression.line` nullable.
- I-7 keyscan's ask rule is added first; a no stops the switch.
- I-8 both READMEs added to FR2; body text, rule label and test messages renamed.
- M-1 runctl unregister in a terminal tab, in the delete list; M-2 A3 greps with `-F -f`; M-3 key assembled by the builder; M-4 `chmod +x` via a terminal tab.
