# appReso

Per-app CPU and memory rollup on macOS.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- appreso
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

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
