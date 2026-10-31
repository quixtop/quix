---
name: shipped
author: shrix
description: "(shrix) List the last n features shipped (default 25) as a table from the project's deplog — smoke state, dep time, feature, machine verdict. -v / -u filter verified / unverified; -w opens the smoke-check widget. Read-only. Triggers on /shipped [n], 'what shipped', 'what went out lately', 'features shipped', 'last few features'."
metadata:
  version: "1.0"
  category: workflow
---

# shipped — What Went Out (last n features, from the deplog)

## Meaning
`/shipped [n]` answers "what actually shipped lately?" from the project's
deplog — the durable record every `dep` writes. It REPORTS; it never edits
the log, never re-derives history from git, never triggers a dep.

## Source
- `docs/logs/deplogs.md` in the CURRENT project (the same file the `dep`
  skill maintains, newest-first). Read it directly — no git archaeology.
- Missing file → say "no deplog in this project — nothing has been shipped
  via `dep` yet" and stop. Do not scan other projects, do not invent rows.
- Project-scoped: only THIS repo's log, never another project's.

## Options
All optional, any order, freely combined (`/shipped 50 -u`, `/shipped -u 50`):

| option | aliases | effect |
|--------|---------|--------|
| `n` | — | how many features to list (default **25**) |
| `-w` | `--widget`, `widget` | render the tickable checklist, not the table |
| `-v` | `--verified`, `verified` | only `✓` machine-verified |
| `-u` | `--unverified`, `unverified` | only `⚠` and `–` |
| `-h` | `--help` | describe the skill, don't run it |

Bare `/shipped` = 25 features, all glyphs, as a table. `n` is numeric and the
aliases are words, so they never collide — `/shipped 50 unverified` parses
cleanly.

Short flags bundle: `-wu` ≡ `-w -u` ≡ `-uw` ≡ `--widget --unverified`. All
four parse identically; never reject a spelling that is unambiguous.

### The count
- `n` = how many FEATURES (table rows) to show, newest first. Default **25**.
- `n` counts FEATURES, not deps. Walk the deplog newest-first, emitting one
  row per feature. A dep that shipped 6 features contributes 6 rows.
- **`n` is a FLOOR, not a ceiling — always finish the day.** Once `n` rows
  exist, note the DATE of the row that reached it, then keep going until
  every remaining feature from that same date is listed. Stop at the first
  dep dated earlier. A day is never shown in part: the table's oldest date
  is always a complete day's record.
- So the real total is `n` or more. When it overshoots, say so in the note
  line — "28 features · 25 asked, 02Aug26 completed".
- Read only as far back as needed — as far as the day-completion requires
  and no further. Don't parse a 2,000-line deplog for `n=25`.
- Non-numeric, zero, or negative `n` → use the default and note it in one
  line. Fewer than `n` features in the log → show them all and say so
  ("only k features logged").
- A no-op dep writes no entry, so every row here is a
  feature that really shipped.

### The filter
- **`-` counts as UNVERIFIED.** It means no evidence was recorded either
  way — not proof of a pass. `-u` is a worklist, so it over-includes rather
  than silently dropping something that may still need eyes.
- `-v` and `-u` are mutually exclusive. Both given → say so in one line and
  use the default (all).
- **`n` counts rows AFTER filtering.** `/shipped -u` yields 25 unverified
  features, reading back as far as that takes — the point is a full worklist,
  not a sample of recent deps. Say the span in the note line: "25 unverified
  · 18Jul26–05Aug26".
- Day-completion (above) applies to the FILTERED set: the oldest date shown
  holds all of that day's *matching* features, not all of its features.
- Nothing matches → one line ("nothing unverified — all 25 carry `✓`"), never
  an empty table.
- Legend lists only the glyphs actually present in the filtered table.
- `-h`, `--help` or `help` as the sole argument: print this skill's
  description and how to invoke it, then stop.

## Widget mode (`-w`) and verilog reports
The DEFAULT rendering is the table in `## Columns`. When `-w` is passed, READ
`references/widget.md` first — it holds the widget build and how reports are
recorded to `docs/logs/verilog.md`.

## Columns
Four columns, one row PER FEATURE — the default markdown table. `-w` renders the
deps' `[chk]` CHECKS instead, one row per check (`references/widget.md` § Rows):
smoke state is recorded per check, and a check is not a feature. The two axes sit
at OPPOSITE ends so they can never be misread for each other: the owner's smoke
leads the row, the machine's read-only verdict trails it.

    | smoke | dep            | features                     | auto |
    |-------|----------------|------------------------------|------|
    |  ✅   | 29Jul26/9.05p  | TG delete/edit sync          |  ✓   |
    |       |                | ranged media (>8MB streams)  |  ⚠   |
    |  ❌   | 29Jul26/2.05p  | reaction-hover reactor faces |  ⚠   |

- **smoke** (leftmost) — the OWNER's result, from `docs/logs/verilog.md`,
  which records it PER CHECK. In the table it is the dep's SUMMARY, printed on
  the dep's FIRST row only (continuation rows blank, like `dep`): ❌ if any of
  its checks failed, else ⬜ if any is untested, else ✅; `–` when the dep listed
  no checks; ⬜ when there is no verilog yet. Under `-w` every check row carries
  its OWN state and is the interactive control — the GESTURES below apply to
  widget rows only.

  | glyph | state | gesture | row text |
  |-------|-------|---------|----------|
  | – | the dep listed no checks (table summary only) | — | normal |
  | ⬜ | not tested | — | normal |
  | ✅ | passed | click | muted, struck through |
  | ❌ | failed | shift-click | normal weight, NOT struck |

  Styling is deliberately asymmetric: strikethrough reads as "done, ignore",
  so striking a failure would bury the one row that needs attention.
- **auto** (rightmost) — the MACHINE's read-only verdict; defined below.
- Each WIDGET row (a check) carries an internal **ID** — its 1-based position
  among that dep's `[chk]` items in the deplog, the same number `verilog.md` and
  `dep` use, stable because deplog entries are append-only and never renumber.
  NEVER displayed; it rides in the report payload. Table rows (features) carry no
  ID — they are never reported on.

- **dep** — the entry's `[DDMonYY/H.MMx]` timestamp verbatim, printed only
  on the dep's FIRST row; continuation rows leave it blank. Never merge a
  dep's features into one crammed cell.
- **features** — condensed from the entry's `>` summary line and its
  **Deployed** bullets: one short phrase per shipped capability/fix
  (~35 chars; keep proper nouns and version-critical qualifiers). Include
  only what SHIPPED — skip process bullets (tests, review outcomes, push
  notes, deploy mechanics); those feed the glyph, not the rows.
- **auto** — judged PER FEATURE from the entry's own evidence sections
  (Verified / Tests / Live / Pending), never from the smoke column:
    - `✓` machine-verified — the entry's tests/live evidence covers it
    - `⚠` shipped but awaiting the owner's smoke — the entry names it in
      Pending, "owed", or "not machine-verified"
    - `–` no verification recorded for it either way
  A dep's features routinely split between these (code paths green while a
  visual awaits eyes) — that split is the point of a per-feature verdict.
  ⚠️ Never infer one axis from the other. A row can be machine-verified AND
  owner-passed, or shipped with automation unsure and the owner finding it
  broken. Both are normal.
- End with a two-line legend, one per axis.
- Keep each row within the terminal width when one is known; shorten
  feature phrases before ever letting a row wrap.
