# proj-tasks

A one-line glance at the project's task file with priorities.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- proj-tasks
```

## Usage

Invoke it as `/proj-tasks` in Claude Code.

One-line glance at the PROJECT task files (the tasks family: TODO.md, docs/tasks.md, docs/tasks/…) with priorities — read-only. `/proj-tasks -f` adds the project status view: completion and active tasks, recent pushes, uncommitted and unpushed work, smoke-check state of what shipped, system health (tests, build, docs, CI, dependencies) and the next step. Use when checking pending project tasks, prioritizing next work, session planning, or asking for the project's status. NOT the personal todo manager — use /todo.

## Source

`skills/proj-tasks` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
