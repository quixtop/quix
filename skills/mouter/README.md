# mouter

Route each task to the best-fit model tier and effort, with background quality checks. Needs: skill-creator, Codex CLI, jq, Python 3.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/mouter
```

## Requires

- [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) — to build or extend it
- [Codex CLI](https://github.com/openai/codex) — optional adapter
- [jq](https://github.com/jqlang/jq)
- [Python 3](https://www.python.org)

## Usage

Invoke it as `/mouter` in Claude Code.

Routes each task to the best-fit model tier and effort, running background quality agents on spare plan capacity. Triggers on \"mouter\" or its subcommands (status, config, table, set, reset, refresh, throttle, toggle); on which-model or how-much-effort questions; on usage caps or maximizing a flat-rate plan; on delegate/parallelize/background/subagent requests. Not for routing in the user's own code or model-pricing questions.

## Source

`skills/mouter` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
