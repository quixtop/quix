# cc-chk

Watch ~/.claude.json's size with health indicators. Needs: jq, Claude Code.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- cc-chk
```

## Requires

- [jq](https://github.com/jqlang/jq)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — it watches its config

## Usage

```text
cc-chk — monitor Claude Code config file size with health indicators
Reports total ~/.claude.json size plus per-project history-blob byte counts.
Health icons: ✅ healthy | ⚠️ growing | 🚨 cleanup needed
```

## Source

`sh/cc-chk` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
