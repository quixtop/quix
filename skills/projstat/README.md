# projstat

A one-screen project status: tasks, recent work, smoke verification, health.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/projstat
```

## Usage

Invoke it as `/projstat` in Claude Code.

Quick project status dashboard showing tasks, recent work, smoke-verification state (shipped but unverified), and system health

## Source

`skills/projstat` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
