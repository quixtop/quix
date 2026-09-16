# spec

Turn a rough feature idea into an implementation-ready spec through structured questions.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/spec
```

## Usage

Invoke it as `/spec` in Claude Code.

Transform rough feature ideas into implementation-ready specs through structured requirements gathering, design options, and validation. Use to spec out a feature or plan before building — full multi-section specs, not quick ideation (superpowers:brainstorming) or PRD publishing (to-prd).

## Source

`skills/spec` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
