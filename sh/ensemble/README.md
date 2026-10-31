# ensemble

A task ledger for several Claude Code sessions on one project — every task by feature, who has it and where it stands. Needs: Python 3, git.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- ensemble
```

## Requires

- [Python 3](https://www.python.org)
- [git](https://git-scm.com) — run it inside a git repo — the ledger lives in its git dir

## Usage

```text
ensemble — the Ensemble's ledger for the project you are in: every task by FEATURE, so a feature's
rows are its bucket (~/.claude/rules-ref/sessions.md § The ledger). The leader writes; anyone reads.
The file is <git dir>/ensemble/ledger.jsonl — one JSON row per task, never committed.

Usage:
  ensemble add --feature <area:topic> --task "<what>" [--worker 001] [--origin 000]
               [--state queued|running] [--paths a,b] [--spec <path>] [--session <id>]
  ensemble set <id> [--state queued|running|ready|shipped|held] [--worker 001] [--shas a,b]
               [--summary "<1-3 lines>"] [--paths a,b] [--spec <path>] [--session <id>]
  ensemble show [--all] [--json]        open rows (not shipped); --all every row
  ensemble bucket <feature> [--json]    one feature's rows; an area alone (auth) takes all its features
  ensemble since <iso> [--json]         rows updated at or after the time (the /push chatlog)
  ensemble path                         the ledger file's path
  ensemble -h | --help | help
```

## Source

`sh/ensemble` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
