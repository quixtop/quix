# handoff

Write a cold-resume file so a fresh session can continue without the context.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- handoff
```

## Usage

Invoke it as `/handoff` in Claude Code.

Move work to any fresh session that cannot inherit this context — a new session on this machine (CLI, Desktop, IDE), a Projects thread, another agent or machine. Writes a self-deleting HANDOFF.md (`/handoff <topic>` scopes it to that topic), recovers compacted turns, and cold-read-tests it. NOT for mirroring a live session you keep open — use Remote Control.

## Source

`skills/handoff` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
