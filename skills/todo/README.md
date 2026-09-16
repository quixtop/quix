# todo

A personal todo list in a markdown file you choose. Needs: Python 3.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/todo
```

## Requires

- [Python 3](https://www.python.org)

## Usage

Invoke it as `/todo` in Claude Code.

Personal todo list manager backed by a configurable file (default ~/md/todo.md). Use when the user runs /todo to view, add, remove, complete/un-complete items, clear done items, or set the file path. Full subcommand grammar (prefix shorthands, -X/--XYZ flags, comma/range batches) is in the skill body. NOT for project task tracking (use tasks).

## Source

`skills/todo` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
