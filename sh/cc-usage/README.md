# cc-usage

Your Claude plan's usage at a glance — the 5-hour and weekly windows as bars, with when each resets. Needs: Python 3, Claude Code.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- cc-usage
```

Then in Claude Code: `/cc-usage`. The command runs `~/.local/bin/cc-usage` without asking each time.

## Requires

- [Python 3](https://www.python.org)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — signed in — it reads its usage with that sign-in

## Usage

Run `cc-usage -h`.

## Source

`sh/cc-usage` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
