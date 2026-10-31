---
name: runctl
author: shrix
description: "(shrix) Register, unregister, rename, list or run scripts as slash commands via runctl. Triggers on /runctl register <path>, 'register it', 'make this script a slash command'."
argument-hint: 'register <path>|unregister <name>|rename <old> <new>|list|<name> [args]'
allowed-tools: Bash(python3 ~/.agents/skills/runctl/bin/runctl:*)
---

# runctl

Dispatcher for the `runctl` skill. Every mutation and every execution routes
through `~/.agents/skills/runctl/bin/runctl` via the Bash tool.

## Dispatch rule

Parse the first positional token of the user's invocation:

- **If there is no argument** (user typed just `/runctl`) → invoke:

  ```
  python3 ~/.agents/skills/runctl/bin/runctl help
  ```

  This prints the usage and every subcommand.

- If it is one of `register`, `unregister`, `rename`, `list`, `exec`, `help` →
  invoke:

  ```
  python3 ~/.agents/skills/runctl/bin/runctl <subcmd> <remaining-args>
  ```

- Otherwise the token is a registered script name → invoke:

  ```
  python3 ~/.agents/skills/runctl/bin/runctl exec <name> <remaining-args>
  ```

## Auto-description on `register`

When the invocation is `register` and the user did **not** pass `--desc`,
generate the description yourself instead of letting `runctl` fall back to its
stub:

1. Resolve the script path the user gave and **read the file**.
2. Write a single-line description capturing what the script does, its main
   args/modes, and natural-language triggers — match the style of the existing
   commands, e.g.
   `"<what it does> — Triggers on '…', '…'. Args: a | b (default …)"`.
   One line only, no newlines; prefer `—` / `·` / `|` separators over colons.
3. Pass it through: `runctl register <path> [--as …] [--force] --desc "<generated>"`.

If the user *did* pass `--desc`, forward it unchanged. If the script can't be
read or is too trivial to summarize, omit `--desc` and let `runctl` use its
own fallback (the existing description on re-register → the first `#`
comment after the ownership stamp → a stub).

After running `runctl`, include its stdout and stderr in your reply as a
fenced code block — Claude Code collapses raw tool output by default, and
the user shouldn't need `Ctrl+O` to read it. Matters most for `help` and
`list`. Surface a non-zero exit code if `runctl` fails.

## Extras on `register`

`--extras "<instruction>"` attaches a single-line *presentation* instruction to
a registered script. `runctl` stores it in the command file (frontmatter
`x-run-extras:` plus a "Presentation extras" line in the body), so whenever the
`/<name>` command runs, that instruction is part of the injected prompt and you
apply it **when reporting the script's output** — it shapes presentation only,
never how the script runs. Forward `--extras` unchanged when the user supplies
it; it is optional. Example:
`--extras "wrap each value token in backticks so values render blue in CC CLI; leave icon glyphs plain"`.

## Notes

- Do not try to parse arguments or execute scripts yourself. `runctl` is the
  authoritative implementation.
- If the user asks "what scripts do I have?" or "show registered scripts",
  run `runctl list`.
- If the user says "add this script" / "register this script", ask for the
  path (or infer it) and run `runctl register <path>`. Forward any overrides
  the user supplies (`--as`, `--desc`, `--extras`, `--model`, `--effort`,
  `--widget`, `--browser`, `--force`; `runctl help` lists them all).
  When no `--desc` is given, generate one from the script per
  *Auto-description on `register`*.
- See `~/.agents/skills/runctl/README.md` for the full layout and conventions.
