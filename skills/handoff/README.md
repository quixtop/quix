# handoff

Write a cold-resume file so a fresh session can continue without the context.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/handoff
```

## Usage

Invoke it as `/handoff` in Claude Code.

Use when continuing this work in a fresh session that cannot inherit the current context — CLI to the Desktop app, a different agent on this machine, or another machine/the web app IF the project folder is synced there. Writes a disposable, self-deleting HANDOFF.md at the project root for a cold resume; `/handoff <hint>` puts that item first in Next Steps. Not for mirroring a live session you keep open — use Remote Control.

## Source

`skills/handoff` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
