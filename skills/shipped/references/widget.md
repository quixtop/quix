# Widget mode and verilog reports
<!-- author: shrix -->

Read when `-w` is passed.

## Widget mode — opt-in, via `-w`
The DEFAULT rendering is the markdown table in `## Columns`. `-w` swaps it for
an interactive `show_widget` checklist of the same deps, by CHECK instead of by
feature. Never print both — that re-lists the same deps twice.

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
being read — so the table is the default and the widget is opt-in.

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

The two axes and the smoke states are defined ONCE in `## Columns` — do not
restate them here.

## Rows — one per `[chk]` check
- **Range:** the same deps the table would show for `n` (features counted exactly
  as in the table, after any filter); the widget lists EVERY check of each of
  those deps.
- Each dep contributes its `[chk]` items, read from its deplog entry in deplog
  order: row = smoke control · the dep's timestamp (first row only) · the check
  text, condensed to ~45 chars.
- A row's ID is its position among that dep's `[chk]` items — the item number
  `verilog.md` uses — so a report always marks the check the owner ticked.
- A dep with no `[chk]` items shows ONE muted, untickable row: `no smoke checks
  listed`.
- The `auto` column stays in the table: it is judged per FEATURE, and a check is
  not a feature.

**Filtering** — `-v` / `-u` pick DEPS on the MACHINE axis, exactly as `The
filter` defines: `-wu` shows every check of a dep with at least one feature not
`✓`; `-wv` every check of a dep with at least one `✓` feature. Smoke state never
filters; it is shown and marked, not selected on. `-u` is therefore the natural
smoke worklist with no special casing, because `⚠` already means "shipped,
awaiting the owner's smoke".

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

