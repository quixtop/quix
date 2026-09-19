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
clear-nvim-swap — remove Neovim swap files from the swap dir.
Safe by design: refuses to run while nvim is open (live swaps must
not be deleted), and supports a dry run. Clears stale swaps that
trigger the "W325: Ignoring swapfile" warning.

  clear-nvim-swap                 delete stale swap files
  clear-nvim-swap -n | --dry-run  list what would go, delete nothing
  clear-nvim-swap -f | --force    delete even while nvim runs (risky)
  clear-nvim-swap -h | --help     this help
```

## Source

`sh/clear-nvim-swap` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
