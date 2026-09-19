# recall

Search your earlier Claude Code sessions for this project.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- recall
```

## Usage

Invoke it as `/recall` in Claude Code.

> (shrix) Look up EARLIER Claude Code sessions for this project — the ones a /clear or a new window left behind. Answers "what did we do before the clear", "which session had X", "what was I working on yesterday". Reads the raw JSONL transcript store; never edits it. Triggers on /recall, /recall <term>, the previous session", "before the clear", "search my sessions for X". NOT for the current conversation (use /pendings) and NOT for carrying state forward (use /handoff).

## Source

`skills/recall` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
