---
name: shipped
author: shrix
description: "(shrix) List the last n FEATURES shipped as a table — owner smoke state · dep timestamp · feature · machine verdict — read from the project's deplog (docs/logs/deplogs.md, newest-first). n counts FEATURES, not deps; defaults to 25, and always rounds up to finish the day it lands on. Filter the rows with -v (machine-verified) or -u (unverified/unchecked). Add -w to render the interactive smoke-check widget instead of the table, whose reports file into docs/logs/verilog.md — bundles as -wu / -wv. Never edits the deplog, never re-derives from git. Triggers on /shipped [n], 'what shipped', 'what went out lately', 'features shipped', 'last few features'."
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
- A no-op dep writes no entry (per the dep skill), so every row here is a
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
- `-h` / `--help` needs no handling here — the global skill-self-help rule
  covers it for every `author: shrix` skill.

## Widget mode — opt-in, via `-w`
The DEFAULT rendering is the markdown table in `## Columns`. `-w` swaps it for
an interactive `show_widget` checklist. Never print both — the widget carries
every column the table did, so showing both re-lists the same deps twice.

| invocation | renders | rows |
|------------|---------|------|
| `/shipped` | table | all |
| `/shipped -u` · `-v` | table | filtered |
| `/shipped -w` | **widget** | all |
| `/shipped -wu` | **widget** | unverified |
| `/shipped -wv` | **widget** | verified |

`-w` and the filters are ORTHOGONAL — `-w` picks the RENDERING, `-u`/`-v` pick
the ROWS. Neither implies the other, and `-w` alone means "everything,
tickable" (the `-u` + `-v` union), not "unfiltered table".

⚠️ **Why opt-in: a widget costs ~8× the table it replaces** — ~485 tokens
against ~59 for a five-row list, plus a one-off ~6k for the widget guidance on
the session's first render, and it then sits in context for every later turn.
Worth paying when rows are about to be marked; wasted when the answer is only
being read. Most `/shipped` runs are a glance, so glancing is free and marking
is asked for.

⚠️ **`-wv` is not a read-only view.** `-v` filters the MACHINE axis; the
checkbox is the SMOKE axis, and the two are independent — a `✓` row is
routinely still ⬜. "Automation says green, has the owner actually looked?" is
precisely what `-wv` asks, and every one of its rows is tickable. Never reason
from one axis to the other, here or anywhere.

Do NOT auto-substitute a table for an explicit `-w`, even if every row is
already ✅. The flag was typed; honour it. (An empty FILTER is different and
already handled — `The filter` says one line, never an empty table.)

`/dep` is unaffected and takes no `-w`: it always renders the widget. Its
checklist is fresh, unticked items by construction, so there is never a
glance-only case to opt out of.

Row layout, the two axes, and the three smoke states are defined ONCE in
`## Columns` — do not restate them here.

**Filtering** — `-v` / `-u` filter on the MACHINE axis only, exactly as
`The filter` defines. Smoke state never filters; it is shown and marked, not
selected on. `-u` is therefore the natural smoke worklist with no special
casing, because `⚠` already means "shipped, awaiting the owner's smoke".

⚠️ **A filter hides rows, it NEVER narrows the report.** The widget holds the
full smoke state of every dep it covers and reports all of it; only the DISPLAY
is filtered. Reporting just the visible subset would flip every hidden ✅ back
to ⬜, because the payload is full-state by design. Display and payload are
separate concerns.

**Marking** — free and reversible in every direction. Rows never lock, so a
mis-reported check is corrected by re-marking it and reporting again. Repeating
a gesture clears back to ⬜; the other gesture switches directly. Marking is
silent — only the button sends, via `sendPrompt`. Rows open carrying their
state from `docs/logs/verilog.md`, so the widget always shows true state.
Print the hint `click = passed · shift-click = failed · again = clear` under
the list — the modifier is otherwise undiscoverable.

**Report payload** — one line PER DEP, IDs only:

    Smoke-Verified (07Aug26/1.30a): pass 1,2 · fail 3,4

- COMPLETE state for that dep, never a diff. Named under `pass` → ✅; named
  under `fail` → ❌; **every ID not named → ⬜**.
- **Retraction is therefore absence** — clear a row, report, it flips back.
  No retract syntax, and no state the widget must remember between sends.
- Everything cleared on a dep that opened with marks → `pass none`, which
  retracts all of them. No failures → omit the `· fail` half entirely.
- Full state is what makes this safe. `sendPrompt` POPULATES the input box
  rather than sending, so the user may edit or discard it, and a second Report
  overwrites an unsent first. Any diff-based scheme loses that silently; a
  complete set is self-healing — the next report repairs whatever the last
  one missed.
- One Report per turn, for the same reason. Harmless if broken: the later
  message already contains everything the earlier one would have.

**Multi-dep reports** — `dep` covers one dep, but `/shipped` spans many, so a
single Report can touch several:

    Smoke-Verified (07Aug26/1.30a): pass 4 · fail 1
    Smoke-Verified (06Aug26/11.35p): pass 2

- **One line PER DEP**, each independently full-state for that dep. Never merge
  IDs across deps — the numbers are positions within a dep and collide freely
  between them.
- Include a dep's line when it has marks now, OR opened with marks. The second
  half is what makes retraction work: a dep whose marks were all cleared must
  still report (`pass none`), or the clearing is silently lost.
- Omit deps untouched in both states — no line, not `pass none`. A `/shipped`
  over 8 deps where you marked 2 sends 2 lines, not 8.

## Recording a report — `docs/logs/verilog.md`
A report may carry SEVERAL `Smoke-Verified` lines, one per dep — apply each
independently to its own dep section, in the order given. On receiving a
`Smoke-Verified (<dep>): <ids>` line, update
`docs/logs/verilog.md` in the CURRENT project. The file lists EVERY check of
every dep with its state, so it is the complete picture, not a verified-only
subset:

    # Smoke test status

    `07Aug26/4.10a`:
    - ⬜ 1. news digest alternation holds
    - ✅ 2. strm hub Disconnect on one line

    `07Aug26/1.30a`:
    - ✅ 1. restart engine — strm-start
    - ❌ 2. strm Telegram chats load
    - ⬜ 3. news j/k dims and brightens

  Glyphs, not `- [ ]` checkboxes: GFM accepts only a space or `x` between the
  brackets, so a third state would render as literal text beside real boxes.
  The leading `-` keeps each line a list item.

- **Seed from the deplog.** A dep's section lists all its `[chk]` items in
  deplog order, every one ⬜ until reported. Item numbers ARE the IDs.
- **Apply a report as full state**: `pass` IDs → ✅; `fail` IDs → ❌; every
  other item in that dep → ⬜. That single rule covers passing, failing AND
  retraction, and makes a repeat report a no-op.
- **Two levels of order, always maintained**: deps newest-first matching the
  deplog; items by ID ascending within each dep. A report for an older dep
  updates that dep's existing section, never appends at the end.
- **A carried check appears in BOTH deps** — `dep` re-lists unconfirmed items,
  so a ❌ in an older dep and a ✅ in a newer one is the correct record of a
  fix, not a contradiction. Never back-edit the older entry; the newest
  occurrence of a check is its current state.
- Create the file if absent, with the `# Smoke test status` header.
- Only ever touch the deps a report names. Every other dep is untouched.
- Never invent an item — if an ID isn't in that dep's deplog entry, say so
  rather than adding a row.
- ⚠️ Smoke state does NOT change what `/shipped` lists. `-v`/`-u` filter on the
  machine axis, so marking something ✅ never removes it from any view — it
  shipped, it still shows, its smoke glyph simply changes.
- Only record what a report actually names — never infer a check passed.

## Columns
Four columns, one row PER FEATURE — identical whether rendered as the default
markdown table or as `-w` widget rows. The two axes sit at OPPOSITE ends so they can
never be misread for each other: the owner's interactive control leads the
row, the machine's read-only verdict trails it.

    | smoke | dep            | features                     | auto |
    |-------|----------------|------------------------------|------|
    |  ✅   | 29Jul26/9.05p  | TG delete/edit sync          |  ✓   |
    |  ⬜   |                | ranged media (>8MB streams)  |  ⚠   |
    |  ❌   | 29Jul26/2.05p  | reaction-hover reactor faces |  ⚠   |

- **smoke** (leftmost) — the OWNER's result, from `docs/logs/verilog.md`.
  Always renders, even with no verilog yet (every row simply opens ⬜). Leads
  the row because it is the column needing action. Under `-w` it is the
  interactive control; in the table it is the same glyph, read-only — the
  GESTURES below apply to widget rows only.

  | glyph | state | gesture | row text |
  |-------|-------|---------|----------|
  | ⬜ | not tested | — | normal |
  | ✅ | passed | click | muted, struck through |
  | ❌ | failed | shift-click | normal weight, NOT struck |

  Styling is deliberately asymmetric: strikethrough reads as "done, ignore",
  so striking a failure would bury the one row that needs attention.
- **auto** (rightmost) — the MACHINE's verdict, read-only: `✓` verified ·
  `⚠` awaiting the owner's smoke · `–` no evidence either way. Judged from the
  deplog entry, never from the smoke column.
  ⚠️ Never infer one axis from the other. Row 1 is machine-verified AND
  owner-passed; row 3 shipped with automation unsure and the owner finding it
  broken. Both are normal.
- Each row also carries an internal **ID** — its 1-based position in that dep's
  list, stable because deplog entries are append-only and never renumber.
  NEVER displayed; it rides in the report payload and orders the verilog.

- **dep** — the entry's `[DDMonYY/H.MMx]` timestamp verbatim, printed only
  on the dep's FIRST row; continuation rows leave it blank. Never merge a
  dep's features into one crammed cell.
- **features** — condensed from the entry's `>` summary line and its
  **Deployed** bullets: one short phrase per shipped capability/fix
  (~35 chars; keep proper nouns and version-critical qualifiers). Include
  only what SHIPPED — skip process bullets (tests, review outcomes, push
  notes, deploy mechanics); those feed the glyph, not the rows.
- **auto** — judged PER FEATURE from the entry's own evidence sections
  (Verified / Tests / Live / Pending):
    - `✓` machine-verified — the entry's tests/live evidence covers it
    - `⚠` shipped but awaiting the owner's smoke — the entry names it in
      Pending, "owed", or "not machine-verified"
    - `–` no verification recorded for it either way
  A dep's features routinely split between these (code paths green while a
  visual awaits eyes) — that split is the point of a per-feature verdict.
- End with a two-line legend, one per axis.
- Respect the session's table-width cap (the per-prompt terminal-width
  note); shorten feature phrases before ever letting a row wrap.
