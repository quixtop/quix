# fnd

Fast filename search; -s switches to content search. Needs: fd, ripgrep.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/fnd/fnd -o ~/.local/bin/fnd && chmod +x ~/.local/bin/fnd
```

## Requires

- [fd](https://github.com/sharkdp/fd)
- [ripgrep](https://github.com/BurntSushi/ripgrep)

## Usage

```text
fnd — filename search (fd) by default; -s switches to content search (rg).
Searches are case-insensitive by default in BOTH modes; pass --case-sensitive
to override (the underlying tools let the last case-flag win).

A filename pattern containing * or ? is auto-detected as a GLOB (fd -g) —
no flag needed: `fnd 'ab*.mp4'` just works. A pattern is left as regex
instead when it also has ^ $ \ ( ) | , since those only mean something in
regex — this is what keeps `fnd '^ab.*\.mp4$'` running unchanged.

Usage:
  fnd codebuff                     # filename: one pattern (pass-through to fd)
  fnd 'ab*.mp4'                    # filename: glob, auto-detected from the *
  fnd codebuff freebuff            # filename: multi → parallel fd, grouped output
  fnd codebuff, freebuff           # filename: trailing commas tolerated
  fnd -H codebuff freebuff         # filename: flags + multi (use -t=py for valued flags)
  fnd -s TODO                      # content: search TODO in cwd (passes through to rg)
  fnd -s 'TODO|FIXME'              # content: multi-pattern via rg regex alternation
  fnd -s TODO src/ docs/           # content: scope to files/folders (rg trailing paths)
  fnd -s --case-sensitive TODO     # content: force case-sensitive

Note: noglob UX is added via the calling shell alias; this script doesn't see it.
```

## Source

`sh/fnd` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
