# tasks

A one-line glance at the project's task file with priorities.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/tasks
```

## Usage

Invoke it as `/tasks` in Claude Code.

Quick one-line glance at the PROJECT task file (TODO.md / docs/tasks.md) with priorities — read-only, never edits. Use when checking pending project tasks, prioritizing next work, or session planning. NOT the personal todo manager — use /todo for personal todos.

## Source

`skills/tasks` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
