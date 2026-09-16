# cc-xtn

Enable and disable Claude Code plugins, skills and MCP servers; see their token weight. Needs: jq, Claude Code.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/cc-xtn/cc-xtn -o ~/.local/bin/cc-xtn && chmod +x ~/.local/bin/cc-xtn
```

## Requires

- [jq](https://github.com/jqlang/jq)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — it configures it

## Usage

```text
cc-xtn — Claude Code extensions manager

Subcommands:
  enable <name> [<name>...]   enable one or more extensions (auto-detects category)
  disable <name> [<name>...]  disable one or more extensions (auto-detects category)
  status <name>     show current state + category for a name
  list [--enabled|--disabled]
                    enumerate all toggleable extensions, grouped by category
  --enabled         shortcut for `list --enabled`
  --disabled        shortcut for `list --disabled`
  help              show usage

Categories (each has its own toggle mechanism):
  plugin   — settings.json enabledPlugins[X] = true|false
  skill    — ~/.agents/skills/<X>/  ↔  ~/.agents/disabled-skills/<X>/
  command  — ~/.claude/commands/<X>.md  ↔  ~/.claude/disabled-commands/<X>.md
  agent    — ~/.claude/agents/<X>.md  ↔  ~/.claude/disabled-agents/<X>.md
  mcp      — ~/.claude.json mcpServers[X]  ↔  mcpServersDisabled[X]
  hook     — settings.json hooks[<event>][matcher==X]  ↔  hooksDisabled[<event>][...]
             named as <event>:<matcher>, e.g. PreToolUse:Bash or Stop:
```

## Source

`sh/cc-xtn` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
