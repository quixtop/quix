# proj-tasks — the project status view (`/proj-tasks -f`)
<!-- author: shrix -->

READ when `/proj-tasks` gets `-f`, `--full` or `status`. It reads files and git
state; only § System Health runs anything (a fast test suite, `tsc --noEmit`,
`gh run list`, a package audit), and nothing it does writes. Section references
without a file name are to `tasks/SKILL.md`.

## What it reads

| source | first found of | used for |
|---|---|---|
| tasks family | as in § Auto-Detection | the glance (unchanged), Tasks counts, Active Now |
| pushlog / changelog | `docs/logs/pushlog.md`, `docs/pushlog.md`, `CHANGELOG.md`, `HISTORY.md` | Recent Work: the last 3 entries |
| deplog | `docs/logs/deplogs.md` (written by `dep`) | smoke fallback |
| verification record | `docs/logs/verilog.md` (written by `shipped`) | Smoke line |
| git | `git status --porcelain`, `git rev-list --count @{u}..HEAD`, `git log --oneline --grep="checkpoint:" @{u}..HEAD` | Uncommitted / Unpushed / Checkpoints |

**Project name**: the git remote URL's basename, else the folder name.

## Tasks counts and Active Now
- Across every tasks-family file: ✅ completed (`[x]`, ✅), 🔄 active (in
  progress, 🔄), ⏳ pending (`[ ]`, ⏳) → `Tasks: X completed, Y active, Z
  pending (N% complete)`. A file with no countable markers adds nothing; none
  countable at all → omit the line.
- Active Now: every 🔄 item, one per line. None → omit the block.

## Smoke line — from `docs/logs/verilog.md`
- Count ✅ / ❌ / ⬜ rows across recent deps (last ~5)
- **Newest occurrence wins.** `dep` re-lists unconfirmed checks, so the same
  check appears in several deps; count only its latest state or a fixed
  failure gets counted twice — once red, once green
- No verilog yet → fall back to counting `[chk]` items in the deplog
- Print: `🔍 Smoke: 8 passed · 2 failed · 4 untested (oldest 02Aug26)`
- Omit any zero segment. All green → `🔍 Smoke: all 12 passed`
- No deplog → omit the line entirely; this is not "Not configured"
- Read-only. Never tick, infer, or write — `/shipped` owns that.
- Point at the fix, not the detail — never list the individual items here.
  The pointer SPLITS, because `-u` filters the MACHINE axis while these
  counts are on the SMOKE axis, and the two are independent:
  - any ❌ → `/shipped -w` — a failure can sit on a machine-`✓` row, which
    `-wu` would hide; unfiltered is the only view guaranteed to hold it
  - ⬜ only → `/shipped -wu` — the worklist, since `⚠` already means
    "shipped, awaiting the owner's smoke"
  Both are `-w` forms: the point of the suggestion is to go TICK something,
  and plain `-u` renders a read-only table.

## Git workflow
- Uncommitted: modified + staged files.
- Unpushed: commits ahead of the upstream.
- 🔖 Checkpoints: UNPUSHED checkpoint commits only
  (`git log --oneline --grep="checkpoint:" @{u}..HEAD`; no upstream → without
  `@{u}..HEAD`). Pushed ones are history: squashing them would need a
  force-push, so they never count. Show the last one's subject.

## 💡 Next — the first that applies
1. any ❌ smoke → "fix the failing smoke check → `/shipped -w`" (a known-broken
   thing that shipped outranks everything below)
2. uncommitted files → "commit or checkpoint the N uncommitted files → `/push`"
3. ⬜ untested only → "smoke-test what shipped → `/shipped -wu`"
4. clean tree and 3 or more unpushed checkpoints → "squash the unpushed
   checkpoints + push → `/push`"
5. unpushed commits → "`/push` the N unpushed commits"
6. else → "start next task: <top open task>"

## System Health

**Tests**
| check | how | status |
|---|---|---|
| framework configured | `jest.config.*`, `vitest.config.*`, `pytest.ini`, `.mocharc.*`, `Cargo.toml [dev-dependencies]` | Present / Missing |
| test script real | `package.json` `scripts.test` is not `echo "Error: no test specified"` | Real / Placeholder |
| tests pass | `checks.sh has tests` exit 0 (`~/.agents/skills/_shared/scripts/checks.sh`) → "passed on this tree", no run; else `npm test` / `pytest` / `cargo test` only if it finishes in under 30 s | Pass / Fail / Skipped |

**Build**
| check | how | status |
|---|---|---|
| build script | `package.json` `scripts.build`, `Makefile`, `Cargo.toml` | Present / Missing |
| TypeScript compiles | `tsconfig.json` present → `tsc --noEmit` | Pass / Fail / N/A |
| build warnings | the last build output, when one is on record | Clean / Warnings |

**Docs**
| check | how | status |
|---|---|---|
| README | `README.md` at the root | Present / Missing |
| README freshness | its last change vs the latest code commit | Fresh (< 30 days) / Stale |
| docs folder | `docs/` | Present / Missing |
| API docs | `docs/api*`, `openapi.yaml`, `swagger.json` | Present / Missing |

**CI (optional)** — GitHub Actions on the current branch:
`BR=$(git branch --show-current)`; empty (detached HEAD) → `CI: skipped
(detached HEAD)`; else `gh run list --branch "$BR" --limit 3 --json
status,conclusion,name,createdAt` → `✅ CI: last 3 runs passing (main)` ·
`⚠️ CI: 1/3 runs failed — "<name>" <age>` · `❌ CI: pipeline broken — "<name>"
failing since <date>`. No `gh` → `CI: not checked (gh CLI not available)`; a
non-GitHub remote → `CI: not checked (non-GitHub remote)`; no runs → `CI: no
workflows configured`.

**Dependencies (optional)** — only with a lockfile:

| lockfile | audit | outdated |
|---|---|---|
| `package-lock.json` | `npm audit --json` | `npm outdated` |
| `pnpm-lock.yaml` | `pnpm audit --json` | `pnpm outdated` |
| `yarn.lock` | `yarn audit --json` | `yarn outdated` |
| `Cargo.lock` | `cargo audit` | `cargo outdated` |
| `requirements.txt` / `poetry.lock` | `pip-audit` | `pip list --outdated` |

Cap the audit at ~10 s (`timeout 10s <cmd>` where `timeout` exists); unavailable
or the cap fires → `Dependencies: audit skipped (slow)`. No lockfile →
`Dependencies: no package manager detected`. Always show the vulnerability
count when the audit succeeds (`❌ 2 critical vulnerabilities (run npm audit
for details)`); the outdated count is supplementary (`⚠️ 3 outdated packages
(1 major, 2 minor)`).

## Output

```
📊 <Project> — status

<the glance, exactly as /proj-tasks prints it>
Tasks: X completed, Y active, Z pending (N% complete)

Recent Work (last 3 pushes):
- <date> <title>
- <date> <title>
- <date> <title>

🔍 Smoke: N passed · N failed · N untested (oldest <date>)

📝 Uncommitted: X modified, Y staged · ⬆️ Unpushed: N · 🔖 Checkpoints: N (last: "<subject>")
💡 Next: <the first rule above that applies>

System Health:
✅ Tests: <status>
✅ Build: <status>
✅ Docs: <status>
[CI: <status> — only if the CI check ran]
[Dependencies: <status> — only if the dependency check ran]

Active Now:
🔄 <active task>

Read: <every file read, comma-separated>
```

## When a source is missing — never an error

| case | shows |
|---|---|
| no tasks file | the glance's own message; suggest creating `docs/tasks.md` |
| no pushlog or changelog | `Recent Work: none yet`; suggest creating `CHANGELOG.md` |
| a file with no entries | `no entries yet` for that section, with a one-line example of a first entry |
| empty or malformed entries | parseable entries only, plus `(N unreadable skipped)` |
| not a git repo | omit the 📝 line |
| no upstream | `⬆️ Unpushed: no upstream` |
| unreadable file | name it and the permission problem (suggest `chmod` or checking ownership); carry on |
