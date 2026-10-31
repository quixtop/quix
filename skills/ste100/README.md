# ste100

Check architecture docs against ASD-STE100 Simplified Technical English and render a colour-coded sheet of what to fix.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- ste100
```

## Usage

Invoke it as `/ste100` in Claude Code.

Check a project's architecture docs against ASD-STE100 Simplified Technical English (Issue 9) and render docs/arch/ste100.html — a colour-coded drawing sheet of the project's STE compliance plus an STE overview — and the docs/arch.html hub with two tabs: System (archify's docs/arch/archify.html, the default) and STE100. Proposes STE rewrites, applied only on a yes. Use when asked to check or rewrite docs in STE / Simplified Technical English.

## Source

`skills/ste100` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
