# mf

Spotlight search from the terminal — the first 50 matches, or as many as you ask.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- mf
```

## Usage

```text
mf — Spotlight search from the terminal (mdfind), the first 50 results by default.

Usage:
  mf <query>                      first 50 matches
  mf -n | --limit <N> <query>     first N matches
  mf -a | --all <query>           every match
  mf -h | --help | help

Words after the options form one query: mf anthropic claude = mf 'anthropic claude'.
Examples:
  mf 'anthropic | claude'
  mf -n 20 'pdf documents'
  mf -a 'important files'
```

## Source

`sh/mf` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
