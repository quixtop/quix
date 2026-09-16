# appReso

Per-app CPU and memory rollup on macOS.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/appReso/appReso -o ~/.local/bin/appReso && chmod +x ~/.local/bin/appReso
```

## Usage

```text
appReso — per-app CPU/memory rollup on macOS.

  appReso <appName> [appName...]     totals per app
  appReso -v <appName>               + the individual processes

Rolls every process belonging to an app into one row, which is the whole
point: modern browsers and Electron apps fan out into dozens of helper
processes, so a plain `ps | grep` shows fragments rather than a footprint.
```

## Source

`sh/appReso` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by worx publish — edit freely; remove this line to keep your edits -->
