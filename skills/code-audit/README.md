# code-audit

A read-only health audit of the whole repository, reported in one place. Needs: Codex CLI.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/code-audit
```

## Requires

- [Codex CLI](https://github.com/openai/codex) — through its clodex pass

## Usage

Invoke it as `/code-audit` in Claude Code.

Use when asked for a comprehensive audit or health review of the whole repo/codebase — 'audit this repo', 'full audit', 'codebase health check', 'review the whole project', periodic quality sweep. Read-only: reports findings, never modifies anything. NOT for reviewing a diff, branch, or PR (use /code-review directly or the code-review plugin).

## Source

`skills/code-audit` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
