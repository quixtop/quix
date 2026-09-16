# ss

Rename macOS screenshots to bare numbers — no date, no prefix.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/ss/ss -o ~/.local/bin/ss && chmod +x ~/.local/bin/ss
```

## Usage

```text
ss — rename macOS screen captures to bare numbers (1.png), no date, no prefix.

macOS names captures "Screenshot 2026-08-20 at 8.25.39 PM.png" and cannot be
made to produce "1.png" natively: setting com.apple.screencapture
name+include-date gets you "ss 1.png", and the collision separator is always
a SPACE with no key to change it. So rename after the fact.

  ss                    rename captures in the screenshot folder
  ss -n | --dry-run | dry-run
                        show what would change, rename nothing
  ss -l | --list | list [n]
                        list the screenshot folder, newest first
                        (default 10 rows; `n` or `all` for more)
  ss -x | --delete | del [n...]
                        move screenshots to the trash (recoverable).
                        Bare form takes the newest numbered one; otherwise
                        name them: `ss del 5 7 9` or `ss del 5, 7, 9`
  ss -r | --reorder | reo | reorder
                        compact existing numbers into 1..N by capture time
  ss -m | --max | max <num>
                        ceiling for THIS run (default below)
  ss -d | --dir | dir <dir>
                        source folder (default ~/Downloads/Down)
  SS_DEST=<dir>         destination (default <source>/Screenshots)
  ss -h | --help | help this help

Every option takes all three forms — short, long, and bare word. reorder
additionally accepts `reo`. Bare words are safe here because ss has no
free-form positionals for one to collide with.

── The number ceiling ──────────────────────────────────────────────────────
Numbers live in 1..MAX (default 99, so filenames stay two digits). Once past
PRESSURE_PCT, free slots are handed out LOWEST FIRST, so deleting 50.png puts
50 back in the pool and a later capture reclaims it.

That deliberately trades away chronological numbering: after 99 the next may
be 50, then 73. The capture ORDER is still recoverable — renaming
never touches mtime, so sorting by date always works. Only the number stops
tracking time, which is the price of a bounded range.

Within one run, files are still processed oldest-first, so a batch gets
ascending slots from whatever the pool offers.

── Where files live ────────────────────────────────────────────────────────
macOS drops captures in DIR; ss renames AND moves them into DIR/Screenshots
so the download folder stays uncluttered. The slot scan reads the destination,
since that is where the numbering state actually lives.

── Fullness indicator ──────────────────────────────────────────────────────
Below TAG_PCT the status line stands alone. At or above it a second, indented
line reports the REMAINING slots — "2 left for max" — coloured by the GYR ramp
from REFS/palettes.html. Its own line, so the status line above keeps its
plain outcome colour and the two readings never compete.
At the default 99/75 that means the line shows for counts of 25 and lower.
Bands are quadratic, so red means genuinely last-slot rather than merely low.
TAG_PCT sits BELOW PRESSURE_PCT on purpose: the colour warns you well before
numbering actually starts jumping backwards into recycled slots.

Renames only files still carrying macOS's own capture names. Anything you
named yourself is never touched. No watcher, no agent, no state file — the
folder itself is the state.
```

## Source

`sh/ss` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix
