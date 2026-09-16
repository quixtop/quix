# pushlog

Summarise the diff since the last push into a pushlog entry.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/pushlog
```

## Usage

Invoke it as `/pushlog` in Claude Code.

Generate a pushlog entry documenting git changes — deterministic bash script computes paths/timestamp/diff range, LLM summarizes the filtered diff into bullets, secret-verifier gates the result. Runs the chatlog skill first. Use when logging git changes before a push.

## Source

`skills/pushlog` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
