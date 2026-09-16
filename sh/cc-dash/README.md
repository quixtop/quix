# cc-dash

Open the Claude Code sessions dashboard in your browser.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/cc-dash/cc-dash -o ~/.local/bin/cc-dash && chmod +x ~/.local/bin/cc-dash
```

## Usage

```text
cc-dash — launch the Claude Code dashboard in the default browser

Starts the dashboard server (Next.js, ~/.claude/dashboard) on PORT if it
isn't already running, waits up to 15s for it to bind, then opens the URL.
Pure dashboard launcher — does not start or interact with any Claude session.
```

## Source

`sh/cc-dash` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
