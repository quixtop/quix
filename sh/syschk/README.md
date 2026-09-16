# syschk

macOS diagnostics in one run — CPU, memory, disk, thermal, top processes.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/syschk/syschk -o ~/.local/bin/syschk && chmod +x ~/.local/bin/syschk
```

## Usage

```text
syschk.sh — macOS System Diagnostics
Detects CPU hogs, ghost/orphaned processes, memory pressure, thermal throttling,
disk pressure, suspicious launch agents, network anomalies, and Claude Code ecosystem issues.

Usage:
  syschk.sh              # Full report
  syschk.sh -q           # Quick scan (CPU + memory + thermal)
  syschk.sh -v           # Verbose (extra detail)
  syschk.sh --cpu        # CPU section only
  syschk.sh --mem        # Memory section only
  syschk.sh --proc       # Process analysis only
  syschk.sh --disk       # Disk section only
  syschk.sh --net        # Network section only
  syschk.sh --therm      # Thermal section only
  syschk.sh --fix        # Plan + one confirmation, then apply safe fixes
```

## Source

`sh/syschk` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
