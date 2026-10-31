# perm-asks

Count the permission prompts Claude Code showed you and list what still asks — split at your last settings.json commit when ~/.claude is in git, else the last 3 days. Needs: Python 3, Claude Code.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- perm-asks
```

## Requires

- [Python 3](https://www.python.org)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — it reads its session transcripts

## Usage

```text
perm-asks — count the permission prompts Claude Code sessions showed you.

Reads every session and subagent transcript under ~/.claude/projects
(read-only) and
counts, per tool call, whether you were asked: allowed once, rejected, or
answered "always" without a matching rule. Blocks (hook, classifier, safety
check) are counted apart. AskUserQuestion / ExitPlanMode are questions, not
permission prompts, and are listed apart. Sessions under /tmp are skipped.

Usage: perm-asks [-d <days>] [-s <when>] [-n <top>] [-v]
  With no -d or -s, the counts split at the last commit that changed
  ~/.claude/settings.json: "after" runs from it to now, "before" covers the
  same length of time before it (at most 7 days), and the top asks list
  only "after" — what still asks. No such commit → the last 3 days.
  -d, --days <n>    window, last n days; no split unless -s is given
  -s, --split <t>   split at t instead, ISO local time (2026-10-26T13:00)
  -n, --top <n>     rows in the top-asks lists (default 10)
  -v, --verbose     one example command per row, cut to 120 characters;
                    only safe shapes are shown (program, subcommand, flags,
                    paths, LAN addresses, URL hosts) — every other value is …
  -h, --help        this help
```

## Source

`sh/perm-asks` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
