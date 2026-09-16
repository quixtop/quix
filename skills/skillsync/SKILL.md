---
name: skillsync
author: shrix
description: (shrix) Audit & repair the shrix skill naming/identity convention (symlink, author, (shrix) prefix, name match). Run /skillsync to audit, /skillsync --fix to repair, /skillsync add <name> to onboard a skill.
---

# skillsync

Audits every shrix skill (identified by `author: shrix` in its `SKILL.md`) in
`~/.agents/skills/` and `~/.agents/disabled-skills/` for the 4-part naming/identity
convention. With `--fix`, repairs drift.

Note: Commands managed by `runctl` are out of scope — use `runctl list` for those.

## Usage

Run the audit script via Bash, appending the user's subcommand words verbatim
(nothing for a plain audit):

```
python3 ~/.agents/skills/skillsync/scripts/skillsync.py [--fix | add <name>]
```

### Subcommands

- *(no args)* — full audit of all shrix skills
- `--fix` — repair NEEDS-FIX skills (name, author, description prefix, symlink)
- `add <name>` — onboard a single skill: fix convention + create/repair symlink.
  `<name>` is the plain skill name (e.g. `foo`).
  If the skill is in `disabled-skills`, prints a clear message and exits non-zero.
  Reports each step (what was fixed vs already compliant) and ends with `/<name>`.

## What it checks (per shrix skill)

1. `~/.claude/skills/<name>` symlink exists and points at `../../.agents/skills/<name>`
2. SKILL.md frontmatter `name:` equals `<name>` (the dir name)
3. `author: shrix` present in frontmatter
4. `description:` value starts with `(shrix)`

## Output groups

- **OK** — enabled skills with no issues
- **NEEDS-FIX** — enabled skills with failing checks (listed per skill)
- **DISABLED** — disabled skills (informational; shown with issues if any)
- **WARN** — orphaned (dangling) symlinks in `~/.claude/skills/`: either leftovers pointing
  at a disabled skill (disabled skills must keep no symlink) or truly broken links. Report-only.

## `--fix` mode

Repairs NEEDS-FIX skills: repoints wrong-target symlinks (delete + recreate), creates
missing ones, sets `name:`, adds `author: shrix`, adds `(shrix) ` prefix to `description:`.
Never touches real files/dirs — a name collision with an installed skill at
`~/.claude/skills/<plain>` is reported, not auto-resolved. Never renames dirs.
