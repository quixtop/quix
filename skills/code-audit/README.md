# code-audit

A read-only health audit of the whole repository, reported in one place. Needs: Codex CLI.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- code-audit
```

## Requires

- [Codex CLI](https://github.com/openai/codex) — through its clodex pass

## Usage

Invoke it as `/code-audit` in Claude Code.

Audit or health review of the whole repo — 'audit this repo', 'full audit', 'codebase health check', 'review the whole project', periodic quality sweep. Read-only: reports verified findings and the trend since the previous audit; writes only its revlogs entry. NOT for a diff, branch or PR (use /code-review).

## Source

`skills/code-audit` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
