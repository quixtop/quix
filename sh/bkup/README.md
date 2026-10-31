# bkup

Copy a folder into a backup folder — new and changed files only; old versions are kept, and nothing is deleted unless you approve. Needs: rsync from Homebrew.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- bkup
```

## Requires

- [rsync](https://formulae.brew.sh/formula/rsync) — brew install rsync — the one macOS ships is too old

## Usage

```text
bkup — copy a folder into a backup folder: new and changed files only; nothing is deleted unless you approve.

The source is only ever read. Old versions of changed files are kept in
<dest>/.deleted/<date>. Files that are gone from the source stay in the backup
until you approve moving them to <dest>/.deleted/<date>; .deleted itself is
emptied only by `purge`, after a y/N. Both questions need you at the keyboard.

Usage:
  bkup nvme ssd                     /Volumes/NVMe2TB/shrix → /Volumes/SSD2TB/nvme-shrix-bkup
  bkup ssd nvme                     /Volumes/SSD2TB/shrix  → /Volumes/NVMe2TB/ssd-shrix-bkup
  bkup <source> <dest>              any folder → any folder (never one inside the other)
  bkup <…> -a | --approve | approve list files gone from the source; on y, move them to .deleted
  bkup <…> -p | --purge | purge     show what .deleted holds; on y, empty it
  bkup -h | --help | help

A destination under /Volumes/<drive> is refused unless that drive is mounted.
Needs Homebrew rsync (/opt/homebrew/bin/rsync); macOS's openrsync lacks options used here.
Log: ~/Library/Logs/bkup.log
Exit: 0 done (✓, or ⚠ when something needs your attention) · 1 failed, refused or partial (✗ / ⚠)
```

## Source

`sh/bkup` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
