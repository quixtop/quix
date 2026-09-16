# shipped

The last n features shipped, as a table, with your own smoke-test state.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/shipped
```

## Usage

Invoke it as `/shipped` in Claude Code.

List the last n FEATURES shipped as a table — owner smoke state · dep timestamp · feature · machine verdict — read from the project's deplog (docs/logs/deplogs.md, newest-first). n counts FEATURES, not deps; defaults to 25, and always rounds up to finish the day it lands on. Filter the rows with -v (machine-verified) or -u (unverified/unchecked). Add -w to render the interactive smoke-check widget instead of the table, whose reports file into docs/logs/verilog.md — bundles as -wu / -wv. Never edits the deplog, never re-derives from git. Triggers on /shipped [n], 'what shipped', 'what went out lately', 'features shipped', 'last few features'.

## Source

`skills/shipped` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
