# refactor

Refactor, optimise and keep a codebase consistent without changing behaviour.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/refactor
```

## Usage

Invoke it as `/refactor` in Claude Code.

Refactoring, performance optimization, code maintenance, architecture consistency, and structured code review. Use when code is slow, has smells/duplication/dead code, needs pattern consistency, or before a PR review.

## Source

`skills/refactor` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
