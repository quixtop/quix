# recall

Search your earlier Claude Code sessions for this project.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/recall
```

## Usage

Invoke it as `/recall` in Claude Code.

> (shrix) Look up EARLIER Claude Code sessions for this project — the ones a /clear or a new window left behind. Answers "what did we do before the clear", "which session had X", "what was I working on yesterday". Reads the raw JSONL transcript store; never edits it. Triggers on /recall, /recall <term>, the previous session", "before the clear", "search my sessions for X". NOT for the current conversation (use /pendings) and NOT for carrying state forward (use /handoff).

## Source

`skills/recall` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
