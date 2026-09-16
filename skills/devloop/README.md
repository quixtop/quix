# devloop

Run an already-reviewed plan to completion unattended, one commit per task.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/devloop
```

## Usage

Invoke it as `/devloop` in Claude Code.

Implement an already-planned, user-reviewed plan to completion, unattended — a flat set of TASKS, or PHASES each holding tasks: per task anchor → test → implement → verify → isolated review → refactor+docs → commit; an exit gate at every phase boundary (once at the end for a flat plan); a compaction-proof ledger; a close proving every plan item shipped green. NOT planning — input is a reviewed plan. Not for a single task or exploratory work. OFFER it and get a yes first; never auto-run. Triggers on handing over a reviewed plan to run unattended.

## Source

`skills/devloop` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
