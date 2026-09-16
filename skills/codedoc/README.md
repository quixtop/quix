# codedoc

Generate, verify and update code documentation — READMEs, changelogs, release notes.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/codedoc
```

## Usage

Invoke it as `/codedoc` in Claude Code.

Generate, verify, update, explain, and changelog code documentation — READMEs, API docs/docstrings, migration guides, release notes. Use when asked to document code, check docs against reality, explain a module, or write release notes.

## Source

`skills/codedoc` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
