# pushlog

Summarise the diff since the last push into a pushlog entry. Needs: chatlog.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- pushlog
```

## Requires

- [chatlog](https://github.com/quixtop/quix/blob/main/skills/chatlog/README.md) — runs first, every time

## Usage

Invoke it as `/pushlog` in Claude Code.

Generate a pushlog entry documenting git changes — deterministic bash script computes paths/timestamp/diff range, LLM summarizes the filtered diff into bullets, secret-verifier gates the result. Runs the chatlog skill first. Use when logging git changes before a push.

## Source

`skills/pushlog` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
