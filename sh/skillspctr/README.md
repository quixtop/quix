# skillspctr

Scan an agent skill for risky code before you install it — a folder, a collection, a .zip or a git URL; static, no API key, nothing leaves the machine. Needs: SkillSpector.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- skillspctr
```

Then in Claude Code: `/skillspctr`. The command runs `~/.local/bin/skillspctr` without asking each time.

## Requires

- [SkillSpector](https://github.com/NVIDIA/skillspector) — the scanner it runs

## Usage

```text
skillspctr — thin wrapper around `skillspector scan`.

  skillspctr <path|url> [extra skillspector args...]

Always runs a static scan (`scan --no-llm`, no API key required) with OSV.dev
unreachable (no dependency name leaves the machine), and decides
`--recursive` automatically from the shape of <path>:

  * directory containing SKILL.md directly        -> single skill   (no --recursive)
  * directory whose subdirs contain SKILL.md      -> skill collection (--recursive)
  * a .md file / .zip / git URL / file URL        -> scanned as-is   (no --recursive)

Anything after <path> is forwarded verbatim to skillspector, e.g.
  skillspctr ./my-skill -f json -o report.json

Note: kept bash-3.2 safe (macOS default) — no arrays, no `set -u`.
```

## Source

`sh/skillspctr` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
