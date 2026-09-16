# prayer

Re-read every rule file in full and comply from here on.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/prayer
```

## Usage

Invoke it as `/prayer` in Claude Code.

Re-read every rule in ~/.claude/rules/ and ~/.claude/CLAUDE.md in full and comply with all of them strictly from this turn onward — picking up any rule edits made since the session started. Forward-acting only: never audits, never grades past turns, never summarises or reprints the rules. Use after a compaction, when a session has drifted, before risky or long unattended work, or on /prayer, 'follow the rules', 'comply', 'stay on the rails'.

## Source

`skills/prayer` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
