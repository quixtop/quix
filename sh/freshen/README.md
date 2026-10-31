# freshen

Update a skill or Homebrew formula at most once a day, just before you use it; a skill update is scanned for secrets and risky code first and rolled back on a hit. Needs: Node.js, Homebrew, Python 3, git, keyscan, skillspctr — and ~/.agents kept in git for skill updates.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- freshen
```

## Requires

- [Node.js](https://nodejs.org) — npx runs the skills CLI
- [Homebrew](https://brew.sh) — for formula updates
- [Python 3](https://www.python.org)
- [git](https://git-scm.com) — each skill update is kept or rolled back in ~/.agents's git
- [keyscan](https://github.com/quixtop/quix/blob/main/sh/keyscan/README.md) — scans each skill update for secrets
- [skillspctr](https://github.com/quixtop/quix/blob/main/sh/skillspctr/README.md) — scans each skill update for risky code

## Usage

```text
freshen — update an installed external skill or Homebrew formula just before its
first use in 24 hours (strict-scope.md, owner 31Oct26): a name checked at 9:00 is
not checked again before 9:00 the next day.
  freshen <name>...                check each name not checked in the last 24 h
  freshen -f | --force <name>...   check even inside those 24 h
  freshen -n | --dry-run <name>... say what would run; change and record nothing
  freshen -h | --help | help
<name> is one of:
  a skill in ~/.agents/.skill-lock.json — DO_NOT_TRACK=1 npx -y skills@latest
    update <name> -g -y, into ~/.agents/skills/<the CLI's folder name>. The new
    version is scanned in place BEFORE anything is kept: keyscan --strict (secrets)
    and skillspctr (static skill scan; it fails above risk score 50). Both clean →
    only that folder is committed in ~/.agents (git commit -- <folder>, so other
    staged work is never touched). A hit, a scan that could not run, a failed
    commit or an interrupt (Ctrl-C, a closed tab) → the folder and the skills lock
    go back to their earlier versions (files a gitignore hides, e.g. node_modules,
    are left as they are); a run that died before that is restored by the next.
  a Homebrew formula — brew upgrade --formula <name>, old versions kept on disk
Skipped, and said so: your own skills (author: shrix), plugins (Claude Code updates
them per marketplace), unknown names. One freshen runs at a time: a second one
waits for nothing — it says so and checks nothing.
Run it outside the sandbox (a Terminal tab): it needs npm, GitHub and /opt/homebrew.
State: ~/.cache/freshen/<name> holds the epoch of the last good check
(FRESHEN_STATE moves it; FRESHEN_NOW stands in for the clock, for tests).
Log: ~/Library/Logs/freshen.log, one line per check (FRESHEN_LOG).
Exit: 0 every name current, updated or skipped · 1 a check failed (the committed
version stays in use) · 2 a restore failed (the line says what to run) · 64 usage.
```

## Source

`sh/freshen` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
