# subcodex

Delegate named tasks to background Codex workers, keep working, then verify their results. Needs: Codex CLI, jq.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/subcodex
```

## Requires

- [Codex CLI](https://github.com/openai/codex)
- [jq](https://github.com/jqlang/jq)

## Usage

Invoke it as `/subcodex` in Claude Code.

Delegate named tasks to background Codex worker(s), keep working, then verify/grade/integrate each result. ONLY invoke when the user explicitly delegates a task to Codex — e.g. "/subcodex <task>", "do X over subcodex", "run this in the bkgd over codex". subcodex DELEGATES work; it is NOT clodex (which debates a question). Do not trigger on incidental mentions.

## Source

`skills/subcodex` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
