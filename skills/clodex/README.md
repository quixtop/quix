# clodex

Claude and Codex in a multi-round dialectic — propose, cross-criticise, converge. Needs: Codex CLI, jq.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/clodex
```

## Requires

- [Codex CLI](https://github.com/openai/codex)
- [jq](https://github.com/jqlang/jq)

## Usage

Invoke it as `/clodex` in Claude Code.

Multi-round Claude+Codex dialectic (default 3, max 5 rounds). Propose, cross-critique, synthesize. ONLY invoke when the user EXPLICITLY uses clodex as an action — e.g. "/clodex <query>", "use clodex on X", "settle this with clodex". Do NOT trigger on incidental mentions, meta-questions about the skill, or code containing the word.

## Source

`skills/clodex` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
