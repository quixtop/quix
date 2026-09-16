# subcodex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `subcodex` skill — CC delegates named tasks to background Codex worker(s), keeps working, then verify→grade→integrates each result — sharing reusable Codex machinery with `clodex` via `_shared/`.

**Architecture:** Approach A (skill-as-orchestrator): the main CC thread drives the Codex job lifecycle via small allowlisted bash helpers in `~/.agents/skills/_shared/`. Write tasks run in isolated git worktrees; read-only tasks run in-place. The same helpers replace clodex's inline launch/poll blocks (full DRY).

**Tech Stack:** Bash (POSIX-ish, `set -euo pipefail`), `jq`, `git` worktrees, the `codex` plugin companion (`codex-companion.mjs`), Markdown skill procedures.

## Global Constraints

- **Skills tree is NOT a git repo.** No `git commit` steps. Each task's gate is its green test run (or, for e2e, the observed behavior). Verbatim from spec §1 note.
- **Dependency-injection seam:** every shared helper invokes Codex via `CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"`. Tests override `CODEX_SH` with a stub. Non-negotiable — it is the test strategy.
- **Dynamic companion path:** resolve newest via `ls -d "$HOME"/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs | sort -V | tail -1`. Never hardcode `1.0.1`.
- **Never `--effort minimal`** (HTTP 400 with Codex's tool config). Min usable `low`.
- **Integration never auto-commits to main.** Codex commits on `subcodex/<slug>` in its worktree; CC applies that diff onto the main tree **unstaged** for user review.
- **`--write` requires a git repo.** Non-git workspace + `--write` → refuse worktree-write; offer read-only or explicit in-place-with-warning.
- **No overclaiming verification:** distinguish "tests ran and failed" (retry) from "verify command could not run" (surface; never claim verified).
- **Isolation boundary:** worktree sandboxes the repo working dir only; absolute-path writes outside the repo are bounded by Codex's own sandbox, not subcodex.
- **Constants:** `MAX_CONCURRENT=4`, `MAX_RETRIES=1`, `STATE_ROOT=/tmp/subcodex-state`, `POLL_TIMEOUT=20min`.
- **Effort matching:** Opus→high, Sonnet→medium, Haiku→low, else high+warn; explicit `--effort` overrides.

## File Structure

**Create — `~/.agents/skills/_shared/`:**
- `codex.sh` — companion wrapper, dynamic path, `--resolve-only` test seam
- `launch-job.sh` — launch `task --background --fresh`, parse job-id, capture logfile
- `poll-job.sh` — poll job to terminal state, write final status (backgroundable)
- `codex-preflight.sh` — `setup --json | jq .ready` auth check
- `codex-effort-match.md` — Claude-model→effort reference table
- `tests/assert.sh` — tiny assertion lib (shared by all helper tests)
- `tests/stub-codex.sh` — fake `codex.sh` emitting canned JSON for offline tests
- `tests/test_codex.sh`, `test_launch-job.sh`, `test_poll-job.sh`, `test_preflight.sh`
- `tests/run.sh` — runs every `_shared/tests/test_*.sh`, reports pass/fail

**Create — `~/.agents/skills/subcodex/`:**
- `scripts/worktree.sh` — `add|path|diff|apply|remove` git-worktree helper
- `references/delegate-prompt.md` — frames the task text handed to Codex
- `references/evaluate-write.md` — verify→grade→decide for write diffs
- `references/evaluate-readonly.md` — sanity-check→grade→decide for analyses
- `references/help.md` — `/subcodex` help block
- `SKILL.md` — the orchestration procedure
- `tests/test_worktree.sh`, `tests/test_skill_structure.sh`, `tests/run.sh`
- `docs/2026-06-29-subcodex-design.md` — the spec (already exists)

**Modify:**
- `~/.agents/skills/clodex/SKILL.md` — point `CODEX_SH` at `_shared/scripts/codex.sh`; swap inline launch (1a/2c/2.6c) → `launch-job.sh`; swap inline pollers (1c/2e/2.6e) → `poll-job.sh`
- `~/.claude/settings.json` — allowlist edits (add `_shared`/`subcodex` patterns; remove the redundant clodex `codex.sh` pattern in the migration task)

**Delete (in clodex migration task):**
- `~/.agents/skills/clodex/scripts/codex.sh`

---

## Task 1: Shared test harness + `codex.sh` wrapper + allowlist

**Files:**
- Create: `~/.agents/skills/_shared/tests/assert.sh`
- Create: `~/.agents/skills/_shared/tests/stub-codex.sh`
- Create: `~/.agents/skills/_shared/tests/run.sh`
- Create: `~/.agents/skills/_shared/tests/test_codex.sh`
- Create: `~/.agents/skills/_shared/scripts/codex.sh`
- Modify: `~/.claude/settings.json:124` (allowlist)

**Interfaces:**
- Produces: `codex.sh <workspace> <subcommand> [args...]` (cd+exec companion); `codex.sh --resolve-only` → prints resolved companion path, exit 0. Resolution reads `$HOME/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs`.
- Produces: `assert.sh` exporting `assert_eq <actual> <expected> <msg>`, `assert_contains <haystack> <needle> <msg>`, `assert_exit <expected-code> <cmd...>`, and a final `assert_summary` that exits nonzero if any assert failed.
- Produces: `stub-codex.sh` — a drop-in `CODEX_SH` replacement keyed by `$STUB_MODE` env.

- [ ] **Step 1: Write `tests/assert.sh`**

```bash
#!/usr/bin/env bash
# Minimal assertion lib for plain-bash tests. Source it; call assert_summary last.
ASSERT_FAILS=0
assert_eq() { # actual expected msg
  if [ "$1" = "$2" ]; then echo "  ok: $3"; else
    echo "  FAIL: $3 — expected [$2] got [$1]"; ASSERT_FAILS=$((ASSERT_FAILS+1)); fi
}
assert_contains() { # haystack needle msg
  case "$1" in *"$2"*) echo "  ok: $3";; *)
    echo "  FAIL: $3 — [$1] does not contain [$2]"; ASSERT_FAILS=$((ASSERT_FAILS+1));; esac
}
assert_exit() { # expected-code cmd...
  local want="$1"; shift; "$@" >/dev/null 2>&1; local got=$?
  if [ "$got" = "$want" ]; then echo "  ok: exit $want for: $*"; else
    echo "  FAIL: exit $want expected, got $got for: $*"; ASSERT_FAILS=$((ASSERT_FAILS+1)); fi
}
assert_summary() {
  if [ "$ASSERT_FAILS" -eq 0 ]; then echo "ALL PASS"; exit 0;
  else echo "$ASSERT_FAILS FAIL(S)"; exit 1; fi
}
```

- [ ] **Step 2: Write `tests/stub-codex.sh`** (canned Codex responses, no real Codex)

```bash
#!/usr/bin/env bash
# Fake codex.sh for offline tests. First arg is workspace (ignored), second is
# the subcommand. Behavior controlled by $STUB_MODE.
# Modes: ready|notready (for `setup`); launch (for `task`); a status-sequence
# file via $STUB_STATUS_FILE (one status per line, consumed across calls).
set -uo pipefail
sub="${2:-}"
case "$sub" in
  setup)
    [ "${STUB_MODE:-ready}" = "ready" ] && echo '{"ready":true}' || echo '{"ready":false}' ;;
  task)
    echo "task-stub-0001 launched (codex stub)" ;;
  status)
    if [ -n "${STUB_STATUS_FIXED:-}" ]; then
      echo "{\"job\":{\"status\":\"$STUB_STATUS_FIXED\",\"logFile\":\"/tmp/stub.log\"}}"
    elif [ -n "${STUB_STATUS_FILE:-}" ] && [ -s "${STUB_STATUS_FILE:-}" ]; then
      s=$(head -1 "$STUB_STATUS_FILE"); sed -i.bak '1d' "$STUB_STATUS_FILE" 2>/dev/null
      echo "{\"job\":{\"status\":\"$s\",\"logFile\":\"/tmp/stub-$s.log\"}}"
    else
      echo '{"job":{"status":"completed","logFile":"/tmp/stub.log"}}'
    fi ;;
  result) echo "STUB RESULT BODY" ;;
  *) echo "{}" ;;
esac
```

- [ ] **Step 3: Write `tests/run.sh`** (runs all `test_*.sh`)

```bash
#!/usr/bin/env bash
# Run every test_*.sh in this dir; exit nonzero if any fail.
set -uo pipefail
cd "$(dirname "$0")"
fails=0
for t in test_*.sh; do
  echo "== $t =="
  bash "$t" || fails=$((fails+1))
done
[ "$fails" -eq 0 ] && echo "SUITE PASS" || { echo "SUITE: $fails file(s) failed"; exit 1; }
```

- [ ] **Step 4: Write the failing test `tests/test_codex.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$DIR/tests/assert.sh"

# Fake HOME with two plugin versions to prove sort -V picks the newest (1.0.10 > 1.0.2)
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
for v in 1.0.2 1.0.10; do
  mkdir -p "$TMP/.claude/plugins/cache/openai-codex/codex/$v/scripts"
  touch "$TMP/.claude/plugins/cache/openai-codex/codex/$v/scripts/codex-companion.mjs"
done
got=$(HOME="$TMP" bash "$DIR/codex.sh" --resolve-only)
assert_contains "$got" "/codex/1.0.10/scripts/codex-companion.mjs" "resolves newest version"

# Bad usage exits 64
assert_exit 64 bash "$DIR/codex.sh" onlyonearg
assert_summary
```

- [ ] **Step 5: Run it — verify it FAILS**

Run: `bash ~/.agents/skills/_shared/tests/test_codex.sh`
Expected: FAIL (codex.sh does not exist yet → resolve test fails / file-not-found).

- [ ] **Step 6: Write `_shared/scripts/codex.sh`**

```bash
#!/usr/bin/env bash
# Shared Codex companion wrapper. Dynamically resolves the newest installed
# codex plugin companion (robust to version bumps), cds into the workspace, and
# forwards all args to codex-companion.mjs.
#   codex.sh <workspace-dir> <subcommand> [args...]
#   codex.sh --resolve-only          # print resolved companion path, exit (test seam)
set -euo pipefail

resolve_companion() {
  ls -d "$HOME"/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs \
    2>/dev/null | sort -V | tail -1
}

if [ "${1:-}" = "--resolve-only" ]; then
  c=$(resolve_companion); [ -n "$c" ] || { echo "codex.sh: no companion found" >&2; exit 70; }
  echo "$c"; exit 0
fi

if [ $# -lt 2 ]; then
  echo "usage: codex.sh <workspace-dir> <subcommand> [args...]" >&2; exit 64
fi
WORKSPACE="$1"; shift
[ -d "$WORKSPACE" ] || { echo "codex.sh: workspace dir missing: $WORKSPACE" >&2; exit 66; }
COMPANION="$(resolve_companion)"
[ -n "$COMPANION" ] || { echo "codex.sh: no companion found" >&2; exit 70; }
cd "$WORKSPACE"
exec node "$COMPANION" "$@"
```

- [ ] **Step 7: Run it — verify it PASSES**

Run: `bash ~/.agents/skills/_shared/tests/test_codex.sh`
Expected: `ALL PASS`.

- [ ] **Step 8: Add allowlist entries** to `~/.claude/settings.json`

Replace the single line 124 (`"Bash(bash ~/.agents/skills/clodex/scripts/codex.sh:*)",`) by INSERTING these above it (leave the clodex line in place for now — it is removed in Task 10):

```json
      "Bash(bash ~/.agents/skills/_shared/scripts/codex.sh:*)",
      "Bash(bash ~/.agents/skills/_shared/scripts/launch-job.sh:*)",
      "Bash(bash ~/.agents/skills/_shared/scripts/poll-job.sh:*)",
      "Bash(bash ~/.agents/skills/_shared/scripts/codex-preflight.sh:*)",
      "Bash(bash ~/.agents/skills/subcodex/scripts/worktree.sh:*)",
      "Bash(mkdir -p /tmp/subcodex-state*:*)",
      "Bash(rm -rf /tmp/subcodex-state*:*)",
      "Bash(ls -1td /tmp/subcodex-state*:*)",
      "Write(/tmp/subcodex-state/**)",
```

- [ ] **Step 9: Validate settings.json is still valid JSON**

Run: `jq -e . ~/.claude/settings.json >/dev/null && echo OK`
Expected: `OK`. (No commit — skills tree unversioned; green test is the gate.)

---

## Task 2: `launch-job.sh`

**Files:**
- Create: `~/.agents/skills/_shared/scripts/launch-job.sh`
- Test: `~/.agents/skills/_shared/tests/test_launch-job.sh`

**Interfaces:**
- Consumes: `codex.sh` via `${CODEX_SH:-…}`.
- Produces: `launch-job.sh <workspace> <statedir> [task-flags...] <prompt>` — runs `task --background --fresh "$@"`, writes `<statedir>/launch.log`, `<statedir>/jobid.txt`, `<statedir>/logfile.txt`; echoes the job-id to stdout. Exit 71 if job-id unparseable. Seams: `LOGFILE_RETRIES` (5), `LOGFILE_WAIT` (0.5).

- [ ] **Step 1: Write failing test `tests/test_launch-job.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$DIR/tests/assert.sh"
SD="$(mktemp -d)"; trap 'rm -rf "$SD"' EXIT

out=$(CODEX_SH="$DIR/tests/stub-codex.sh" LOGFILE_WAIT=0 \
  bash "$DIR/launch-job.sh" /tmp "$SD" --write --effort high "do the thing")
assert_eq "$out" "task-stub-0001" "echoes parsed job-id"
assert_eq "$(cat "$SD/jobid.txt")" "task-stub-0001" "writes jobid.txt"
assert_eq "$(cat "$SD/logfile.txt")" "/tmp/stub.log" "writes logfile.txt"
assert_summary
```

- [ ] **Step 2: Run — verify FAIL**

Run: `bash ~/.agents/skills/_shared/tests/test_launch-job.sh`
Expected: FAIL (launch-job.sh missing).

- [ ] **Step 3: Write `_shared/scripts/launch-job.sh`**

```bash
#!/usr/bin/env bash
# Launch a Codex task in the background; capture job-id + logfile into a statedir.
#   launch-job.sh <workspace> <statedir> [task-flags...] <prompt>
# Echoes the job-id. Seam: CODEX_SH (default _shared/scripts/codex.sh).
set -euo pipefail
CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"
LOGFILE_RETRIES="${LOGFILE_RETRIES:-5}"; LOGFILE_WAIT="${LOGFILE_WAIT:-0.5}"

WS="$1"; STATEDIR="$2"; shift 2
mkdir -p "$STATEDIR"
# Write launch output to the log file ONLY — stdout must carry just the job-id
# (callers do JOBID=$(launch-job.sh ...)). tee-to-stdout would pollute the capture.
bash "$CODEX_SH" "$WS" task --background --fresh "$@" > "$STATEDIR/launch.log" 2>&1

JOBID=$(grep -oE 'task-[a-z0-9]+-[a-z0-9]+' "$STATEDIR/launch.log" | head -1)
[ -n "$JOBID" ] || { echo "launch-job.sh: could not parse job-id" >&2; exit 71; }
echo "$JOBID" > "$STATEDIR/jobid.txt"

LOG=null
for _ in $(seq 1 "$LOGFILE_RETRIES"); do
  LOG=$(bash "$CODEX_SH" "$WS" status "$JOBID" --json 2>/dev/null | jq -r '.job.logFile // "null"') || LOG=null
  [ "$LOG" != "null" ] && [ -n "$LOG" ] && break
  sleep "$LOGFILE_WAIT"
done
echo "$LOG" > "$STATEDIR/logfile.txt"
echo "$JOBID"
```

- [ ] **Step 4: Run — verify PASS**

Run: `bash ~/.agents/skills/_shared/tests/test_launch-job.sh`
Expected: `ALL PASS`.

---

## Task 3: `poll-job.sh`

**Files:**
- Create: `~/.agents/skills/_shared/scripts/poll-job.sh`
- Test: `~/.agents/skills/_shared/tests/test_poll-job.sh`

**Interfaces:**
- Consumes: `codex.sh` via `${CODEX_SH:-…}`.
- Produces: `poll-job.sh <workspace> <jobid> <out-status-file>` — loops `status --json` until `.job.status ∈ {completed,failed,cancelled}`, writes that status to out-file, exit 0. Backgroundable (harness notifies on exit). Seam: `POLL_INTERVAL` (2).

- [ ] **Step 1: Write failing test `tests/test_poll-job.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$DIR/tests/assert.sh"
SD="$(mktemp -d)"; trap 'rm -rf "$SD"' EXIT
# status sequence: running, running, completed
printf 'running\nrunning\ncompleted\n' > "$SD/seq.txt"
OUT="$SD/status.txt"
CODEX_SH="$DIR/tests/stub-codex.sh" STUB_STATUS_FILE="$SD/seq.txt" POLL_INTERVAL=0 \
  bash "$DIR/poll-job.sh" /tmp task-stub-0001 "$OUT"
assert_eq "$(cat "$OUT")" "completed" "writes terminal status after polling"
assert_summary
```

- [ ] **Step 2: Run — verify FAIL**

Run: `bash ~/.agents/skills/_shared/tests/test_poll-job.sh`
Expected: FAIL (poll-job.sh missing).

- [ ] **Step 3: Write `_shared/scripts/poll-job.sh`**

```bash
#!/usr/bin/env bash
# Poll a Codex job to terminal state; write final status to out-file. Backgroundable.
#   poll-job.sh <workspace> <jobid> <out-status-file>
# Seams: CODEX_SH, POLL_INTERVAL (secs, default 2). No `set -e`: tolerate transient
# status hiccups inside the loop.
set -uo pipefail
CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"
POLL_INTERVAL="${POLL_INTERVAL:-2}"
POLL_TIMEOUT_SECS="${POLL_TIMEOUT_SECS:-1200}"   # 20 min; 0 = unbounded
WS="$1"; JOBID="$2"; OUT="$3"
while true; do
  s=$(bash "$CODEX_SH" "$WS" status "$JOBID" --json 2>&1 | jq -r '.job.status // "missing"')
  case "$s" in
    completed|failed|cancelled) echo "$s" > "$OUT"; exit 0 ;;
  esac
  if [ "$POLL_TIMEOUT_SECS" -gt 0 ] && [ "$SECONDS" -ge "$POLL_TIMEOUT_SECS" ]; then
    echo "timeout" > "$OUT"; exit 0
  fi
  sleep "$POLL_INTERVAL"
done
```

- [ ] **Step 4: Run — verify PASS**

Run: `bash ~/.agents/skills/_shared/tests/test_poll-job.sh`
Expected: `ALL PASS`.

---

## Task 4: `codex-preflight.sh`

**Files:**
- Create: `~/.agents/skills/_shared/scripts/codex-preflight.sh`
- Test: `~/.agents/skills/_shared/tests/test_preflight.sh`

**Interfaces:**
- Consumes: `codex.sh` via `${CODEX_SH:-…}`.
- Produces: `codex-preflight.sh [workspace]` — exit 0 if `setup --json` reports `.ready==true`, else exit 1. Seam: `CODEX_SH`.

- [ ] **Step 1: Write failing test `tests/test_preflight.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$DIR/tests/assert.sh"
assert_exit 0 env CODEX_SH="$DIR/tests/stub-codex.sh" STUB_MODE=ready    bash "$DIR/codex-preflight.sh" /tmp
assert_exit 1 env CODEX_SH="$DIR/tests/stub-codex.sh" STUB_MODE=notready bash "$DIR/codex-preflight.sh" /tmp
assert_summary
```

- [ ] **Step 2: Run — verify FAIL**

Run: `bash ~/.agents/skills/_shared/tests/test_preflight.sh`
Expected: FAIL (codex-preflight.sh missing).

- [ ] **Step 3: Write `_shared/scripts/codex-preflight.sh`**

```bash
#!/usr/bin/env bash
# Preflight: is Codex authed/ready? exit 0 if ready, 1 otherwise.
#   codex-preflight.sh [workspace]   (default workspace /tmp)
set -uo pipefail
CODEX_SH="${CODEX_SH:-$HOME/.agents/skills/_shared/scripts/codex.sh}"
WS="${1:-/tmp}"
ready=$(bash "$CODEX_SH" "$WS" setup --json 2>/dev/null | jq -r '.ready // false')
[ "$ready" = "true" ]
```

- [ ] **Step 4: Run — verify PASS, then run the whole shared suite**

Run: `bash ~/.agents/skills/_shared/tests/run.sh`
Expected: `SUITE PASS` (all four helper tests green).

---

## Task 5: `codex-effort-match.md` (shared reference)

**Files:**
- Create: `~/.agents/skills/_shared/references/codex-effort-match.md`
- Test: `~/.agents/skills/_shared/tests/test_effort_doc.sh`

**Interfaces:**
- Produces: a reference doc both skills link to for the Claude-model→effort table.

- [ ] **Step 1: Write failing structural test `tests/test_effort_doc.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$DIR/tests/assert.sh"
f="$DIR/codex-effort-match.md"
[ -f "$f" ] && body="$(cat "$f")" || body=""
for tok in "Opus" "high" "Sonnet" "medium" "Haiku" "low" "minimal"; do
  assert_contains "$body" "$tok" "mentions $tok"
done
assert_summary
```

- [ ] **Step 2: Run — verify FAIL.** Run: `bash ~/.agents/skills/_shared/tests/test_effort_doc.sh` → FAIL (file absent).

- [ ] **Step 3: Write `_shared/references/codex-effort-match.md`** (verbatim content)

```markdown
# Codex effort matching (shared by clodex + subcodex)

Match Codex reasoning effort to Claude's active model so comparisons/work stay
apples-to-apples. Read the "You are powered by the model named X" line from the
system prompt.

| Detected Claude model | Codex effort |
|---|---|
| Opus (any version)   | `high`   |
| Sonnet (any version) | `medium` |
| Haiku (any version)  | `low`    |
| Anything else        | `high` + warn |

- An explicit `--effort` flag always overrides this default.
- **Never use `--effort minimal`** — returns HTTP 400 with Codex's tool config.
- If detection fails, default to `high` and warn the comparison may not be
  apples-to-apples.
```

- [ ] **Step 4: Run — verify PASS.** Run: `bash ~/.agents/skills/_shared/tests/test_effort_doc.sh` → `ALL PASS`.

---

## Task 6: `subcodex/scripts/worktree.sh`

**Files:**
- Create: `~/.agents/skills/subcodex/scripts/worktree.sh`
- Test: `~/.agents/skills/subcodex/tests/test_worktree.sh`
- Create: `~/.agents/skills/subcodex/tests/run.sh` (trivial per-dir runner — copy the 8-line `_shared/tests/run.sh` from Task 1 Step 3 verbatim; a generic harness, not logic worth DRYing)
- **DRY:** subcodex tests SOURCE `~/.agents/skills/_shared/tests/assert.sh` directly — do NOT create a local `subcodex/tests/assert.sh` copy

**Interfaces:**
- Produces: `worktree.sh <add|path|diff|apply|remove> <repo-dir> <slug>`. `add` → creates branch `subcodex/<slug>` + worktree under `<git-common-dir>/subcodex-worktrees/<slug>`, records base SHA in `<…>/<slug>.base`, prints worktree path. `diff` → net diff vs base. `apply` → applies that diff onto `<repo-dir>` working tree **unstaged** (plain `git apply`, no `--index`; fails non-zero on conflict for SKILL.md to handle). `remove` → removes worktree + branch. Exit 65 if `<repo-dir>` is not a git repo.

- [ ] **Step 1: Write failing test `tests/test_worktree.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$HOME/.agents/skills/_shared/tests/assert.sh"
WT="$DIR/scripts/worktree.sh"
REPO="$(mktemp -d)"; trap 'rm -rf "$REPO"' EXIT
git -C "$REPO" init -q
git -C "$REPO" config user.email t@t; git -C "$REPO" config user.name t
printf 'hello\n' > "$REPO/file.txt"
git -C "$REPO" add file.txt; git -C "$REPO" commit -qm init

# non-git dir → exit 65
NG="$(mktemp -d)"; assert_exit 65 bash "$WT" add "$NG" foo; rm -rf "$NG"

# add → worktree + branch exist
path=$(bash "$WT" add "$REPO" job1)
assert_contains "$path" "subcodex-worktrees/job1" "add prints worktree path"
[ -d "$path" ] && ok=yes || ok=no; assert_eq "$ok" "yes" "worktree dir exists"
git -C "$REPO" branch --list subcodex/job1 | grep -q job1 && b=yes || b=no
assert_eq "$b" "yes" "branch subcodex/job1 exists"

# make a change in the worktree, commit it
printf 'world\n' >> "$path/file.txt"
git -C "$path" commit -aqm "codex change"

# diff shows it
d=$(bash "$WT" diff "$REPO" job1); assert_contains "$d" "+world" "diff shows change"

# apply onto main repo working tree, UNSTAGED (porcelain shows ' M', not staged)
bash "$WT" apply "$REPO" job1
st=$(git -C "$REPO" status --porcelain file.txt)
assert_contains "$st" "file.txt" "apply brings change into main tree"
assert_eq "$(git -C "$REPO" diff --cached --name-only)" "" "apply leaves it unstaged"

# remove cleans up
bash "$WT" remove "$REPO" job1
[ -d "$path" ] && g=yes || g=no; assert_eq "$g" "no" "worktree removed"
assert_summary
```

- [ ] **Step 2: Run — verify FAIL.** Run: `bash ~/.agents/skills/subcodex/tests/test_worktree.sh` → FAIL (worktree.sh missing).

- [ ] **Step 3: Write `subcodex/scripts/worktree.sh`**

```bash
#!/usr/bin/env bash
# Manage subcodex git worktrees for isolated write tasks.
#   worktree.sh add    <repo> <slug>   -> create worktree+branch, print path
#   worktree.sh path   <repo> <slug>   -> print worktree path
#   worktree.sh diff   <repo> <slug>   -> net diff of branch vs base
#   worktree.sh apply  <repo> <slug>   -> apply diff onto repo working tree (unstaged)
#   worktree.sh remove <repo> <slug>   -> remove worktree + branch
set -euo pipefail
CMD="${1:-}"; REPO="${2:-}"; SLUG="${3:-}"
[ -n "$CMD" ] && [ -n "$REPO" ] && [ -n "$SLUG" ] || {
  echo "usage: worktree.sh <add|path|diff|apply|remove> <repo> <slug>" >&2; exit 64; }
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || {
  echo "worktree.sh: not a git repo: $REPO" >&2; exit 65; }

# --git-common-dir can be relative (e.g. ".git") under -C; force it absolute
git_common_dir="$(git -C "$REPO" rev-parse --git-common-dir)"
[ "${git_common_dir:0:1}" = "/" ] || git_common_dir="$REPO/$git_common_dir"
WT_ROOT="$git_common_dir/subcodex-worktrees"
WT="$WT_ROOT/$SLUG"; BR="subcodex/$SLUG"; BASEF="$WT_ROOT/$SLUG.base"

case "$CMD" in
  add)
    mkdir -p "$WT_ROOT"
    base=$(git -C "$REPO" rev-parse HEAD)
    git -C "$REPO" worktree add -b "$BR" "$WT" "$base" >&2
    echo "$base" > "$BASEF"
    echo "$WT" ;;
  path) echo "$WT" ;;
  diff)
    base=$(cat "$BASEF" 2>/dev/null || echo HEAD)
    git -C "$WT" diff "$base" ;;
  apply)
    # plain apply → lands UNSTAGED in the working tree (no --index/--3way staging).
    # On conflict (parallel edits to the same files) apply fails non-zero; SKILL.md
    # catches that and resolves/surfaces it — conflict handling lives at the skill level.
    base=$(cat "$BASEF" 2>/dev/null || echo HEAD)
    git -C "$WT" diff "$base" | git -C "$REPO" apply - ;;
  remove)
    git -C "$REPO" worktree remove --force "$WT" 2>/dev/null || true
    git -C "$REPO" branch -D "$BR" 2>/dev/null || true
    rm -f "$BASEF" ;;
  *) echo "worktree.sh: unknown subcommand: $CMD" >&2; exit 64 ;;
esac
```

- [ ] **Step 4: Run — verify PASS.** Run: `bash ~/.agents/skills/subcodex/tests/test_worktree.sh` → `ALL PASS`.

---

## Task 7: subcodex reference prompts (`delegate`, `evaluate-write`, `evaluate-readonly`, `help`)

**Files:**
- Create: `~/.agents/skills/subcodex/references/delegate-prompt.md`
- Create: `~/.agents/skills/subcodex/references/evaluate-write.md`
- Create: `~/.agents/skills/subcodex/references/evaluate-readonly.md`
- Create: `~/.agents/skills/subcodex/references/help.md`
- Test: `~/.agents/skills/subcodex/tests/test_references.sh`

**Interfaces:**
- Produces: prompt templates referenced by SKILL.md. `delegate-prompt.md` contains placeholder `{{TASK}}`; the evaluate docs encode the verify→grade→decide / sanity→grade→decide steps from spec §6; `help.md` documents the flags from spec §3.4.

- [ ] **Step 1: Write failing test `tests/test_references.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$HOME/.agents/skills/_shared/tests/assert.sh"
R="$DIR/references"
get() { [ -f "$1" ] && cat "$1" || echo ""; }
assert_contains "$(get "$R/delegate-prompt.md")" "{{TASK}}" "delegate has {{TASK}} placeholder"
ew="$(get "$R/evaluate-write.md")"
assert_contains "$ew" "verify" "evaluate-write covers verify"
assert_contains "$ew" "could not run" "evaluate-write distinguishes couldn't-run"
er="$(get "$R/evaluate-readonly.md")"
assert_contains "$er" "sanity" "evaluate-readonly covers sanity-check"
h="$(get "$R/help.md")"
assert_contains "$h" "--write" "help documents --write"
assert_contains "$h" "--verify" "help documents --verify"
assert_summary
```

- [ ] **Step 2: Run — verify FAIL.** → FAIL (files absent).

- [ ] **Step 3: Write `references/delegate-prompt.md`** (verbatim)

```markdown
# subcodex delegate prompt

You are an autonomous Codex worker invoked by Claude Code to complete ONE
delegated task. Work only within the given workspace. When done, summarize:
(1) what you changed or found, (2) how to verify it, (3) any assumptions.

For write tasks: make the change AND commit it on the current branch with a
clear message. Do not touch files unrelated to the task.

TASK:
{{TASK}}
```

- [ ] **Step 4: Write `references/evaluate-write.md`** (verbatim — operationalizes spec §6.1)

```markdown
# Evaluating a write task result

1. **Verify** — run the verify command IN THE WORKTREE (explicit `--verify`, else
   the inferred project test/build). Capture output to `verify.log`.
2. **Grade** — Did tests/build pass? Does the diff actually satisfy the task
   intent (not merely compile)? Read `worktree.sh diff`.
3. **Decide:**
   - PASS → `worktree.sh apply` the diff onto the main tree (UNSTAGED, never
     auto-commit). On conflict, resolve — never discard; surface non-trivial
     conflicts to the user.
   - Tests RAN and FAILED → retry up to MAX_RETRIES, re-delegating with the
     failure log as context; then fallback (CC finishes it / surfaces to user).
   - Verify command COULD NOT RUN (missing/errored) → surface this; do NOT claim
     "verified". Distinguish this case from a genuine test failure.
```

- [ ] **Step 5: Write `references/evaluate-readonly.md`** (verbatim — spec §6.2)

```markdown
# Evaluating a read-only task result

1. **Sanity-check** — spot-check the analysis's claims against the real code;
   do not trust assertions blindly.
2. **Grade** — relevance and quality for the pipeline step that needs it.
3. **Decide:** PASS → use as pipeline input; FAIL → retry once or discard with a
   short note on why.
```

- [ ] **Step 6: Write `references/help.md`** (verbatim — spec §3)

```markdown
# /subcodex — delegate tasks to background Codex worker(s)

Usage:
  /subcodex <task>                      one read-only task, in place
  /subcodex --write <task>              write task in an isolated worktree
  /subcodex --verify "<cmd>" --write <task>   write task; CC runs <cmd> to verify
  /subcodex <task1> ; <task2> ; ...     batch: one Codex job per task

Flags:
  --write              write-capable Codex in a git worktree (default: read-only)
  --verify "<cmd>"     verification command for the eval step (default: inferred)
  --effort LEVEL       low|medium|high|xhigh (default: matched to Claude's model)
  --model <m>          override Codex model
  --wait               block until done instead of background+notify

Notes:
  - --write requires a git repo (worktree isolation). Non-git → read-only or
    explicit in-place-with-warning.
  - Integration never auto-commits to main; changes land unstaged for review.
  - Disambiguation: subcodex DELEGATES a task; clodex DEBATES a question.
```

- [ ] **Step 7: Run — verify PASS.** Run: `bash ~/.agents/skills/subcodex/tests/test_references.sh` → `ALL PASS`.

---

## Task 8: `subcodex/SKILL.md` (orchestration procedure)

**Files:**
- Create: `~/.agents/skills/subcodex/SKILL.md`
- Test: `~/.agents/skills/subcodex/tests/test_skill_structure.sh`

**Interfaces:**
- Consumes: all `_shared/` helpers (Tasks 1–5), `worktree.sh` (Task 6), `references/*` (Task 7).
- Produces: the user-invocable `subcodex` skill procedure. Content is authored to operationalize spec §3–§9; this task lists the REQUIRED sections and the exact embedded command snippets that must appear verbatim (the structural test enforces them). Prose framing follows the cited spec sections — the implementer has the spec open.

- [ ] **Step 1: Write failing structural test `tests/test_skill_structure.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$HOME/.agents/skills/_shared/tests/assert.sh"
f="$DIR/SKILL.md"; body="$([ -f "$f" ] && cat "$f" || echo "")"
# frontmatter
assert_contains "$body" "name: subcodex" "frontmatter name"
assert_contains "$body" "description:" "frontmatter description"
# required sections / behaviors (operationalizing the spec)
for tok in \
  "Disambiguation" "Confirm" "--write" "--verify" "worktree.sh" \
  "launch-job.sh" "poll-job.sh" "codex-preflight.sh" "registry.jsonl" \
  "MAX_CONCURRENT" "MAX_RETRIES" "unstaged" "evaluate-write" "evaluate-readonly" \
  "Non-git" "delegate-prompt"; do
  assert_contains "$body" "$tok" "SKILL.md covers: $tok"
done
assert_summary
```

- [ ] **Step 2: Run — verify FAIL.** → FAIL (SKILL.md absent).

- [ ] **Step 3: Author `subcodex/SKILL.md`** with these REQUIRED parts:

**Frontmatter** (verbatim):

```markdown
---
name: subcodex
description: Delegate named tasks to background Codex worker(s), keep working, then verify/grade/integrate each result. ONLY invoke when the user explicitly delegates a task to Codex — e.g. "/subcodex <task>", "do X over subcodex", "run this in the bkgd over codex". subcodex DELEGATES work; it is NOT clodex (which debates a question). Do not trigger on incidental mentions.
---
```

**Required sections** (author prose per the cited spec section; MUST include the listed verbatim snippets):

1. **Invocation & disambiguation** (spec §3.1–§3.2) — the three trigger forms; the subcodex-vs-clodex-vs-incidental rule; the one-line ambiguity question.
2. **Confirm-before-launch gate** (spec §3.3) — include the confirm echo block verbatim:
   ```
   subcodex → "<resolved task>"
   mode: <--write (worktree) | read-only>   verify: <cmd|inferred>   effort: <level>
   Proceed? (yes / edit / cancel)
   ```
   Slash form with an unambiguous task may skip; inferred forms always confirm.
3. **Flags & effort match** (spec §3.4) — link `references/help.md` and `~/.agents/skills/_shared/references/codex-effort-match.md`.
4. **Preflight** — `bash ~/.agents/skills/_shared/scripts/codex-preflight.sh || stop with "/codex:setup"`.
5. **State & registry** (spec §4.3) — `STATE_ROOT=/tmp/subcodex-state`; per-job dir layout; append one JSON line per job to `registry.jsonl`; retention sweep (keep newest 10 job dirs). Include the launch snippet verbatim:
   ```bash
   SLUG="$(date +%s)-$(echo "$TASK" | cksum | cut -d' ' -f1)"
   SD="/tmp/subcodex-state/$SLUG"; mkdir -p "$SD"
   # write task.txt mode.txt verify.txt effort.txt via the Write tool
   ```
6. **Worktree setup (write only)** (spec §7):
   ```bash
   WS=$(bash ~/.agents/skills/subcodex/scripts/worktree.sh add "$REPO" "$SLUG")
   # read-only: WS="$REPO"
   ```
   Plus the **Non-git refusal** rule for `--write`.
7. **Launch + poll** (spec §5 steps 3–4):
   ```bash
   JOBID=$(bash ~/.agents/skills/_shared/scripts/launch-job.sh "$WS" "$SD" \
            $([ "$MODE" = write ] && echo --write) --effort "$EFFORT" \
            "$(cat "$SD/prompt.txt")")
   # then start poll-job.sh with Bash run_in_background:true:
   bash ~/.agents/skills/_shared/scripts/poll-job.sh "$WS" "$JOBID" "$SD/status.txt"
   ```
   State that CC continues other work; the harness notifies when the poller exits.
8. **Batch** (spec §5) — split list on `;`/newlines; fan out one job per task; cap `MAX_CONCURRENT=4` in flight; evaluate each as it lands (pipeline, not barrier).
9. **Evaluate on completion** (spec §6) — fetch `result`, then follow `references/evaluate-write.md` (write) or `references/evaluate-readonly.md` (read-only). `MAX_RETRIES=1` then fallback. Apply via `worktree.sh apply` (unstaged); a **non-zero apply exit = conflict** → CC resolves or surfaces to the user, never discards. Write `verdict.md`.
10. **Cleanup** — `worktree.sh remove` after integration; cancel non-terminal jobs from `registry.jsonl` on a fresh invocation (orphan reconciliation).
11. **Failure handling** — reproduce the spec §8 table.
12. **CC-may-propose** rule (spec §3.1 item 3) — CC may suggest delegating, must ask first, never silent.

- [ ] **Step 4: Run — verify PASS.** Run: `bash ~/.agents/skills/subcodex/tests/test_skill_structure.sh` → `ALL PASS`.

- [ ] **Step 5: Run the full subcodex offline suite.** Run: `bash ~/.agents/skills/subcodex/tests/run.sh` → `SUITE PASS`.

---

## Task 9: subcodex end-to-end smoke (real Codex)

**Files:** none created (manual integration verification). Requires `/codex:setup` ready.

**Interfaces:** Consumes the full subcodex skill. Gated on `codex-preflight.sh` exit 0.

- [ ] **Step 1: Preflight.** Run: `bash ~/.agents/skills/_shared/scripts/codex-preflight.sh && echo READY`
  Expected: `READY`. If not, run `/codex:setup` first; if Codex is unavailable, mark this task blocked and proceed to Task 10 (offline suites already prove the units).

- [ ] **Step 2: Read-only e2e.** In a small repo, invoke: `/subcodex summarize what scripts/worktree.sh does`
  Expected observations: confirm gate shows read-only; a `task-…` job launches; CC reports it kept control; on completion the result is fetched, sanity-checked, and summarized. Verify `/tmp/subcodex-state/<slug>/result.md` exists.

- [ ] **Step 3: Write e2e.** In a throwaway git repo with a trivial failing target, invoke:
  `/subcodex --write --verify "bash tests/run.sh" add a no-op helper function to scripts/util.sh`
  Expected: confirm gate shows `--write (worktree)`; worktree `subcodex/<slug>` created; Codex commits there; `verify` runs; on pass the diff is applied to the main tree **unstaged** (`git status` shows it, `git diff --cached` empty); worktree removed; `verdict.md` written.

- [ ] **Step 4: Non-git refusal.** From a non-git dir, invoke `/subcodex --write touch a file`
  Expected: refusal with the read-only / in-place-with-warning offer. No worktree attempted.

---

## Task 10: Migrate clodex to `_shared/` (full DRY)

> **AS-BUILT NOTE (executed):** Done as a **MINIMAL swap** per user decision, not the full
> inline-block swap below. What was actually done: (1) repointed clodex's `CODEX_SH` →
> `~/.agents/skills/_shared/scripts/codex.sh`; (2) dropped the `COMPANION` 1.0.1 hardcode —
> preflight now `bash $CODEX_SH --resolve-only`; (3) deleted `clodex/scripts/codex.sh` + empty dir;
> (4) allowlist line handled earlier. clodex's inline launch/poll blocks (Steps 2–3 below) were
> **left unchanged** — they already call `$CODEX_SH`, so they use the shared wrapper automatically
> (lower regression risk; keeps clodex's tee/timing features). Also: `_shared/` was restructured
> into `scripts/`, `references/`, `tests/` (skill-like layout) per user request; all refs + the
> allowlist updated to `_shared/scripts/...`. Steps 2–3 below are the un-taken full-swap option.

**Files:**
- Modify: `~/.agents/skills/clodex/SKILL.md`
- Delete: `~/.agents/skills/clodex/scripts/codex.sh`
- Modify: `~/.claude/settings.json` (remove redundant clodex codex.sh allowlist line)

**Interfaces:** Consumes `_shared/scripts/codex.sh`, `launch-job.sh`, `poll-job.sh`. Behavior of clodex must remain identical.

- [ ] **Step 1: Repoint the wrapper constant.** In `clodex/SKILL.md`, change the `CODEX_SH` constant to `~/.agents/skills/_shared/scripts/codex.sh` (drop the `COMPANION` hardcode of `1.0.1`; resolution is now dynamic inside the shared wrapper).

- [ ] **Step 2: Swap inline launch blocks.** Replace the launch+jobid+logfile bash in clodex steps **1a, 2c, 2.6c** with calls to `_shared/scripts/launch-job.sh`, preserving each step's timing markers (`r{k}-tstart.txt`) and the `--effort "$(cat …/effort.txt)"` argument. Example for 1a:

```bash
date +%s > "$STATE_DIR/r1-tstart.txt"
JOBID=$(bash ~/.agents/skills/_shared/scripts/launch-job.sh "$INVOKE_CWD" "$STATE_DIR/r1" \
         --effort "$(cat $STATE_DIR/effort.txt)" "$(cat $STATE_DIR/query.txt)")
# jobid.txt/logfile.txt now live in $STATE_DIR/r1/
```

- [ ] **Step 3: Swap inline poller blocks.** Replace clodex steps **1c, 2e, 2.6e** `until … status … done` loops with:

```bash
date +%s > "$STATE_DIR/r1-tclaude.txt"
bash ~/.agents/skills/_shared/scripts/poll-job.sh "$INVOKE_CWD" \
  "$(cat $STATE_DIR/r1/jobid.txt)" "$STATE_DIR/r1-status.txt"
```

(run via Bash `run_in_background: true`, as before). Keep all downstream reads of `r{k}-status.txt`, `r{k}-jobid.txt`, `r{k}-logfile.txt` working — adjust paths to the new `$STATE_DIR/r{k}/` subdir if you nest them, or keep flat naming; pick one and apply consistently across all rounds and the stats/cleanup steps.

- [ ] **Step 4: Delete the old wrapper.** `rm ~/.agents/skills/clodex/scripts/codex.sh`

- [ ] **Step 5: Remove redundant allowlist line.** In `~/.claude/settings.json`, delete the line `"Bash(bash ~/.agents/skills/clodex/scripts/codex.sh:*)",` (the `_shared/scripts/codex.sh` entry added in Task 1 now covers clodex). Validate: `jq -e . ~/.claude/settings.json >/dev/null && echo OK` → `OK`.

- [ ] **Step 6: Grep for stragglers.** Run: `grep -rn "clodex/scripts/codex.sh\|codex/1.0.1" ~/.agents/skills/clodex/SKILL.md` → expect **no matches** (no lingering hardcoded path / old wrapper reference).

---

## Task 11: clodex regression gate (real dialectic)

**Files:** none. The DRY-migration acceptance gate. Requires `/codex:setup` ready.

- [ ] **Step 1: Preflight.** `bash ~/.agents/skills/_shared/scripts/codex-preflight.sh && echo READY` → `READY`.

- [ ] **Step 2: Run a real dialectic.** Invoke: `/clodex --rounds 3 which is better for a config file: TOML or YAML, and why?`
  Expected: R1 launches a Codex job via the shared `launch-job.sh`; pollers fire and notify; R2 critique; synthesis produces a final settled answer WITH the Stats block (Attribution + Time taken). No errors about missing job state, null logfiles, or "missing" status.

- [ ] **Step 3: Confirm parity.** Verify the run reached "clodex DIALECTIC COMPLETE", the Codex `resume` session-ids are listed, and `/tmp/clodex-state/<ts>/` holds the round artifacts. If anything regressed (job not found, poller hang), STOP — the shared helpers don't reproduce clodex's inline logic exactly; diff against the pre-migration behavior and fix `launch-job.sh`/`poll-job.sh` before considering Task 10 done.

---

## Self-Review (completed by plan author)

- **Spec coverage:** §3 control/triggers → Task 8 (SKILL.md) + Task 7 (help). §4 components → Tasks 1–8. §4.3 registry → Task 8 step-3 part 5. §5 lifecycle → Task 8. §6 evaluation → Task 7 (evaluate-*) + Task 8 step-3 part 9. §7 worktree/non-git → Task 6 + Task 8 + Task 9 step-4. §8 failures → Task 8 part 11. §9 clodex migration → Tasks 10–11. §10 tests → Tasks 1–9 tests. All sections mapped.
- **Placeholder scan:** no TBD/TODO; markdown-deliverable tasks (5,7) give verbatim content; SKILL.md (8) gives verbatim frontmatter + required snippets + a structural test enforcing coverage (the one task whose prose is authored from the open spec — flagged explicitly, not a silent placeholder).
- **Type/name consistency:** helper signatures match across producer and consumer tasks — `launch-job.sh <ws> <statedir> [flags] <prompt>` (Task 2 ⇄ Task 8 step-3 part 7 ⇄ Task 10 step 2); `poll-job.sh <ws> <jobid> <out>` (Task 3 ⇄ Task 8 ⇄ Task 10 step 3); `worktree.sh <cmd> <repo> <slug>` (Task 6 ⇄ Task 8). `CODEX_SH` seam consistent everywhere.
```
