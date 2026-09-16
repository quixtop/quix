# skillsync

Audit and repair the naming and identity convention across your skills.

## Install

```bash
d=~/.agents/skills; [ -d "$d" ]||d=~/.claude/skills; mkdir -p "$d" && curl -fsSL https://github.com/quixtop/quix/archive/main.tar.gz | tar -xz -C "$d" --strip-components=2 quix-main/skills/skillsync
```

## Usage

Invoke it as `/skillsync` in Claude Code.

Audit & repair the shrix skill naming/identity convention (symlink, author, (shrix) prefix, name match). Run /skillsync to audit, /skillsync --fix to repair, /skillsync add <name> to onboard a skill.

## Source

`skills/skillsync` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
