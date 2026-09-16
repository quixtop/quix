# test

Generate tests and find coverage gaps in Python, JS and Go.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/test
```

## Usage

Invoke it as `/test` in Claude Code.

Generate tests and analyze test coverage (Python/JS/Go). Use when asked to write/add tests, find coverage gaps, or add a regression test for a bug — NOT for merely running an existing test suite.

## Source

`skills/test` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
