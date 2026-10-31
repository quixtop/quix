---
name: start
author: shrix
description: "(shrix) A project at a glance — unread handoff, where the last session stopped, git, open work, last push and ship, stack, run commands, services by env-var name, docs — then the next move; `--deep` adds a code map. Use when opening, returning to or onboarding onto a project. NOT a past-session search (/recall) or the task list (/proj-tasks)."
metadata:
  version: "3.0"
  category: discovery
---

# start — the project at a glance

| invocation | does |
|---|---|
| `/start` | the card, then the next move (about 3 s) |
| `/start --deep` | the card, then a map of the code from an Explore subagent |

## 1. The card — one Bash call

```bash
python3 ~/.agents/skills/start/scripts/card --session "${CLAUDE_SESSION_ID}"
```

Print its output unchanged, in a `text` block. The card only reads: the
handoff's heading, the last session (`recall-scan.py --latest`, its text
masked), git, the tasks files, the first pushlog and deplog entries, manifests,
env-var NAMES and which docs exist. A line it cannot fill says why. Claude Code
already loads CLAUDE.md, AGENTS.md, the rules, memory and a git status, so
start reads none of them again.

Then add ONE line, **Next** — the single most useful move, first match wins:
1. a handoff file → read it fully and follow it; its own footer says when to
   delete it
2. a ❌ on the Shipped line's smoke → fix the failing check first
   (`/shipped -w`); a known-broken thing that shipped outranks the rest
3. uncommitted or unpushed work → name it
4. the last session's last chapter or ask, if still open → resume it
   (`/recall <id>` for the detail)
5. else the top of `/proj-tasks`

The card glances at the newest entries only; the full status view —
completion, smoke across recent deps, system health — is `/proj-tasks -f`.

## 2. `--deep` — only when asked

After the card, read `references/deep.md` and give its brief to an Explore
subagent in the foreground; print the map it returns (40 lines or fewer). No
CLAUDE.md → offer `/init` (built in; it writes a file, so ask first).

## Never

- open `.env*` (`.env.example` only, names only), `.dev.vars`, `*.tfvars`,
  keys or credential files
- print a value, a URL or a string literal taken from code
- write, fetch or delete anything — start reads

## Hand-offs

| need | skill |
|---|---|
| the task list; pushes, deps and smoke | `/proj-tasks`, `/proj-tasks -f` |
| what shipped and its checks | `/shipped` |
| a past session in detail | `/recall <id>` |
| plan a feature | `/spec` |
| document existing code | `/spec docs` |
| review recent changes | `/rev` |
| audit the repo | `/code-audit` |
