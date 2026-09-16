# start

Build a mental model of an unfamiliar codebase before touching it.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/start
```

## Usage

Invoke it as `/start` in Claude Code.

Establish comprehensive project context by analyzing codebase patterns, architecture, and conventions. Use when onboarding to a new/unfamiliar codebase or (re)building a mental model of a project.

## Source

`skills/start` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
