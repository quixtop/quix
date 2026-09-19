# chatlog

Log a session's decisions and debugging into the project's chatlog.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- chatlog
```

## Usage

Invoke it as `/chatlog` in Claude Code.

Log significant chat interactions from a dev session into the project chatlog (docs/logs/chatlog.md) — project-scoped, newest-first, secret-redacting. Also invoked FIRST by the pushlog push workflow (must complete before pushlog.sh runs).

## Source

`skills/chatlog` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
