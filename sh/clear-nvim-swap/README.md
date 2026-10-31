# clear-nvim-swap

Remove stale Neovim swap files — refuses while nvim is open, supports a dry run. Needs: Neovim, proj-env.sh.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- clear-nvim-swap
```

## Requires

- [Neovim](https://neovim.io)
- [proj-env.sh](https://github.com/quixtop/quix/blob/main/sh/proj-env.sh/README.md) — sourced at start

## Usage

```text
clear-nvim-swap — save and close running nvim sessions, then remove stale
Neovim swap files (the ones behind "E325: ATTENTION" and "W325: Ignoring
swapfile").

Each running nvim is shown — folder and open files — and closed only on
your y: its session is saved first (open with the printed `nvim -S <file>`),
then it quits. Never closed: an nvim with unsaved changes or a running
:terminal, or a suspended (Ctrl-Z) one. A swap file whose nvim still runs
is kept, so answering n is safe.

Usage: clear-nvim-swap [-n|--dry-run|dry-run] [-y|--yes|yes] [-f|--force|force]
  -n, --dry-run   show sessions and swap files, close and delete nothing
  -y, --yes       close every closable session without asking
  -f, --force     skip the sessions and delete every swap file, live ones too
                  (a running nvim's swap is its crash-recovery data)
  -h, --help      this help
```

## Source

`sh/clear-nvim-swap` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
