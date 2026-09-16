---
name: projstat
author: shrix
description: "(shrix) Quick project status dashboard showing tasks, recent work, smoke-verification state (shipped but unverified), and system health"
metadata:
  version: "1.1"
  category: status
effort: low
---

# Project Status Reporter

Quick project health dashboard showing tasks, recent work, and system health.

## Auto-Detection

**Tasks file** (first found):
- `docs/proj/tasks.md`
- `docs/tasks.md`
- `TODO.md`
- `TASKS.md`

**Pushlog/changelog** (first found):
- `docs/logs/pushlog.md`
- `docs/pushlog.md`
- `CHANGELOG.md`
- `HISTORY.md`

**Deplog** (shipping record, written by `dep`):
- `docs/logs/deplogs.md`

**Verification record** (smoke-checks confirmed, written by `shipped`):
- `docs/logs/verilog.md`

**Project name**: Use git remote URL or parent directory name.

---

## Instructions

1. Auto-detect project name from git or directory
2. Find and read tasks file (if exists):
   - Count: ✅ completed, 🔄 active (in progress), ⏳ pending
   - Calculate completion percentage
3. Find and read pushlog (if exists):
   - Show last 3 entries
4. Check git workflow state:
   - Count checkpoint commits (`git log --grep="checkpoint:"`)
   - Count uncommitted changes (modified + staged files)
   - Suggest next action based on state, using this mapping for the 💡 Next line:
     - uncommitted > 0 → "commit or checkpoint the N uncommitted files"
     - clean tree + checkpoints ≥ 3 → "squash checkpoints + push"
     - clean tree, few/no checkpoints → "start next task: <top pending task>"
5. Check system health (test scripts, build config, docs folder)
6. Show currently active tasks
7. Verification state — one line, from `docs/logs/verilog.md`:
   - Count ✅ / ❌ / ⬜ rows across recent deps (last ~5)
   - **Newest occurrence wins.** `dep` re-lists unconfirmed checks, so the same
     check appears in several deps; count only its latest state or a fixed
     failure gets counted twice — once red, once green
   - No verilog yet → fall back to counting `[chk]` items in the deplog
   - Print: `🔍 Smoke: 8 passed · 2 failed · 4 untested (oldest 02Aug26)`
   - Omit any zero segment. All green → `🔍 Smoke: all 12 passed`
   - **A failure outranks an untested item** in the 💡 Next suggestion — ❌ is
     a known-broken thing, ⬜ is merely unknown
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

**If files don't exist**: Show "Not configured" for that section, don't error.

---

## Output Format

```
📊 [Project Name] Project Status

Tasks: X completed, Y active, Z pending (N% complete)

Recent Work (Last 3 Pushes):
- [date] title
- [date] title
- [date] title

🔍 Smoke: N passed · N failed · N untested (oldest [date])

Git Workflow:
🔖 Checkpoints: N (last: "completed task description")
📝 Uncommitted: X modified, Y staged
💡 Next: [context-sensitive suggestion]

System Health:
✅ Tests: [Test framework status]
✅ Build: [Build scripts status]
✅ Docs: [Documentation status]
[CI: last runs status — only if the optional CI/CD check ran]
[Dependencies: audit/outdated — only if the optional dependency check ran]

Active Now:
🔄 [list active tasks]
```

---

## Example Output

(A filled-in instance of the Output Format above — the template is the single
source of truth for structure.)

```
📊 MyApp Project Status

Tasks: 14 completed, 2 active, 2 pending (78% complete)

Recent Work (Last 3 Pushes):
- 15Mar26: Fix auth token refresh
- 14Mar26: Add avatar upload
- 12Mar26: Wire S3 client into upload path

🔍 Smoke: 8 passed · 2 failed · 4 untested (oldest 02Mar26)

Git Workflow:
🔖 Checkpoints: 3 (last: "checkpoint: avatar upload wired")
📝 Uncommitted: 2 modified, 1 staged
💡 Next: commit or checkpoint the 3 uncommitted files

System Health:
✅ Tests: pytest configured, 47/47 passing
✅ Build: build script present
✅ Docs: README + docs/ present
⚠️ CI: 1/3 runs failed — "Deploy to staging" 2h ago
⚠️ Dependencies: 2 outdated packages

Active Now:
🔄 Add email verification flow
🔄 Update API docs for v2 endpoints
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No tasks file found | Project hasn't set up task tracking | Show "Tasks: Not configured" in dashboard; suggest creating `TODO.md` or `docs/tasks.md` |
| No pushlog file found | Project hasn't set up change logging | Show "Recent Work: Not configured" in dashboard; suggest creating `CHANGELOG.md` |
| Malformed data | Tasks or pushlog entries have inconsistent formatting | Show warning for affected section, display parseable data, skip malformed entries |
| Empty file | File(s) exist but contain no entries | Show "No entries yet" for that dashboard section with guidance on adding first entry |
| Permission error | File exists but not readable | Report the permission issue for the specific section and suggest `chmod` or checking ownership |
| Multiple sources found | Both `TODO.md` and `docs/tasks.md` exist for tasks | Use the first match per priority order; note in dashboard footer which sources were used |

---

## CI/CD Pipeline Health (Optional)

If the project uses GitHub Actions or another CI system, include pipeline status in the health dashboard.

### GitHub Actions Check

```bash
# Get status of last workflow runs on the current branch.
# Guard detached HEAD: --show-current prints nothing there, which would malform the gh call.
BR=$(git branch --show-current)
if [ -z "$BR" ]; then echo "CI: skipped (detached HEAD)"; else
  gh run list --branch "$BR" --limit 3 --json status,conclusion,name,createdAt
fi
```

### Dashboard Integration

Add to the System Health section:

```
System Health:
✅ CI: Last 3 runs passing (main)
⚠️ CI: 1/3 runs failed — "Deploy to staging" failed 2h ago
❌ CI: Pipeline broken — "Unit Tests" failing since Mar 15
```

### Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `gh` not installed | GitHub CLI not available | Skip CI section, show "CI: Not checked (gh CLI not available)" |
| Not a GitHub repo | Remote is GitLab, Bitbucket, etc. | Skip CI section, show "CI: Not checked (non-GitHub remote)" |
| No workflow runs found | No CI configured or repo is new | Show "CI: No workflows configured" |

---

## Dependency Health Check (Optional)

Surface security vulnerabilities and stale dependencies. Run only if a package manager lockfile is detected.

### Detection and Commands

| Lockfile | Audit Command | Outdated Command |
|----------|--------------|-----------------|
| `package-lock.json` | `npm audit --json` | `npm outdated` |
| `pnpm-lock.yaml` | `pnpm audit --json` | `pnpm outdated` |
| `yarn.lock` | `yarn audit --json` | `yarn outdated` |
| `Cargo.lock` | `cargo audit` | `cargo outdated` |
| `requirements.txt` / `poetry.lock` | `pip-audit` | `pip list --outdated` |

### Dashboard Integration

```
Dependencies:
✅ No known vulnerabilities
⚠️ 3 outdated packages (1 major, 2 minor)

# Or when issues exist:
❌ 2 critical vulnerabilities (run `npm audit` for details)
⚠️ 5 outdated packages (2 major behind)
```

### When to Skip

- Skip if no lockfile detected (show "Dependencies: No package manager detected")
- Cap the audit at ~10 seconds — run it via `timeout 10s <audit cmd>` where `timeout` exists (coreutils); if it's unavailable or the cap fires, show "Dependencies: Audit skipped (slow)"
- Always show vulnerability count if audit succeeds; outdated count is supplementary

---

## System Health: Specific Checks

The health check in step 5 should look for these concrete indicators:

### Tests

| Check | How | Status |
|-------|-----|--------|
| Test framework configured | Look for `jest.config.*`, `vitest.config.*`, `pytest.ini`, `.mocharc.*`, `Cargo.toml [dev-dependencies]` | Present/Missing |
| Test script exists | Check `package.json` `scripts.test` is not `echo "Error: no test specified"` | Real/Placeholder |
| Tests pass locally | Run `npm test` / `pytest` / `cargo test` (only if fast < 30s) | Pass/Fail/Skipped |

### Build

| Check | How | Status |
|-------|-----|--------|
| Build script exists | Check `package.json` `scripts.build`, `Makefile`, `Cargo.toml` | Present/Missing |
| TypeScript compiles | Look for `tsconfig.json`; if present, `tsc --noEmit` is a quick check | Pass/Fail/N/A |
| No build warnings | Check last build output for warnings | Clean/Warnings |

### Documentation

| Check | How | Status |
|-------|-----|--------|
| README exists | Look for `README.md` in project root | Present/Missing |
| README freshness | Compare `README.md` last modified date vs latest code commit | Fresh (< 30 days) / Stale |
| Docs directory | Look for `docs/` directory | Present/Missing |
| API docs | Look for `docs/api*`, OpenAPI spec files (`openapi.yaml`, `swagger.json`) | Present/Missing |
