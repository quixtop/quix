# clido

A minimal interactive Claude REPL on top of `claude -p`. Needs: Claude Code.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/clido/clido -o ~/.local/bin/clido && chmod +x ~/.local/bin/clido
```

## Requires

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

## Usage

```text
clido — minimal interactive Claude REPL on top of `claude -p`

Usage:
  clido                    Start a new session in the current directory

Input:
  Type your query at the `> ` prompt, press Enter.
  End a line with `\` to continue on the next line (`.. ` prompt appears).

Exit:
  Type `quit`, `exit`, `q`, or `:q`; or press Ctrl-D (EOF) / Ctrl-C.

History:
  Within a single `clido` invocation, turn 2+ continues the conversation
  (via `claude --continue`). Each new `clido` launch starts fresh.
  Continuation is scoped to the current working directory by Claude Code.
```

## Source

`sh/clido` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
