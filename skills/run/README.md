# run

Register any script as a slash command. Needs: Python 3.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/run
```

## Requires

- [Python 3](https://www.python.org)

## Usage

Invoke it as `/run` in Claude Code.

Register arbitrary scripts as slash commands. Triggers on /run register...

## Source

`skills/run` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
