# dep — the report and the deplog (step 5)
<!-- author: shrix -->

READ at step 5 of the pipeline, before printing the report or writing the
deplog entry. Section references without a file name are to `dep/SKILL.md`.

## Dep Report — one table + the checklist widget
A `dep` is a completion, so it ends with the what-shipped table (a table with a
status column), then the developer checklist rendered AS a widget:

1. **What shipped** — the completion status table: a `#` column, one row per
   target, and a status column holding the target's ship id with ✅ / ⚠️ / 🔴
   (version id, tag, digest; "restarted" where a target has no id).
2. **Developer checklist** (checkables, printed LAST) — the dep-unique set, rendered as the
   widget in (3), not as a table: one row per item, its text carrying page/feature, the action
   that proves it works, and the expected result. One row per mod since the
   last `dep`; flag whatever automation couldn't verify or the gate skipped; scope is cumulative —
   carry forward earlier items the user hasn't confirmed testing yet (until smoked).
   ⚠️ Read those carried items from the PREVIOUS deplog entry's **Pending**, never from memory of the
   session. A checklist that depends on recall is lost to the next compaction — the same archaeology
   the dep stamp exists to kill, solved there for the CHANGED set and left unsolved here for the
   CHECKABLE set. Reading it from the file also means the user can see what is outstanding without
   asking. Items they confirm are dropped; the rest are re-listed and land in this dep's own Pending.

   **Confirmation is a FILE, not a chat message.** Drop an item when
   `docs/logs/verilog.md` records it under its dep — never because it was mentioned
   in conversation, which the next compaction loses. Same source-of-truth rule
   as the carried items above.

3. **Checklist widget** — the developer checklist (2) is rendered AS an
   interactive `show_widget`, not as a markdown table. One rendering, never
   both: the widget carries the same rows and can be acted on, so printing a
   table beside it re-lists the same checks twice. Each row's text is the
   `[chk]` phrase itself, which already reads as action-plus-expectation. Spec
   (three-state marking, full-state reporting, hidden IDs, the verilog format) lives
   in the `shipped` skill under "Widget mode", "Columns" and "Recording a
   report" — one definition, both entry points. A checkable's ID is its 1-based
   position among this dep's `[chk]` items as the deplog's **Pending** lists them —
   the widget shows them in that same order, so widget, deplog, verilog and
   `/shipped -w` all number a check alike.
   `dep` and `/shipped -wu` read and write the same file.

## Deplog (persistent key-result log)
Every `dep` that actually did something also records a key-result entry in
`docs/logs/deplogs.md` — the durable record of what shipped. A no-op dep
(change-gate found nothing) writes **no entry**.

- **File / auto-detect**: `docs/logs/deplogs.md`. If missing, create it with a
  header from the project name (git remote basename or dir): `# <ProjectName> Deplog`
  followed by a dashed underline — then proceed.
- **Insert newest-first**: prepend the entry directly after the header block;
  reverse-chronological. **No `---` separators**. **Exactly one blank line
  BETWEEN entries; NO blank lines WITHIN an entry** — the timestamp, summary,
  and every section run tight, back-to-back.
- **Timestamp**: `[DDMonYY/H.MMx]` (x = `a`/`p`), the time the dep ran — a single
  timestamp, never a range. E.g. `[12Jul26/1.07p]`.
- **Entry shape**: the timestamp line, then a `>` **bold summary** line — what
  this dep shipped, lowercase prose (acronyms/proper nouns kept capitalized),
  ending with the **ship id** `(v <sha>)` — with the outgoing id beside it as
  `(v <sha>, prev <sha>)` when the rollback rule captured one; that pair is the
  ONE exception to ids never repeating — and, for published targets, the
  destination `→ <host> (<env>)` (env = prod/staging/… — the highest-stakes fact).
  A dep of SEVERAL deployables puts the LEAD deployable's id in the summary;
  the rest ride the first **Deployed** bullet, one id each — the summary never
  carries more than one id (plus its `prev`).
  A local-only dep has no id — its summary ends `(restarted)` instead.
  The id rides the summary ONCE — never repeated on individual bullets. Then
  the grouped sections below, with no blank line before or between them.
- **Grouped sections** — each is a `**Bold**` header line immediately followed by
  its `- ` bullets (`- ` markers, never `• ` U+2022; no per-bullet timestamps; no
  per-bullet version). Order, **omitting any section with nothing to report**
  (only Deployed is effectively always present, so a clean deploy stays terse):
    1. **Deployed** — the substance: the itemized changes / features / fixes this
       dep shipped, one bullet per notable change. Note the target surfaces/env on
       the header line when useful, e.g. `**Deployed** (both surfaces — …)`.
    2. **Verified** — the proof it works. Two facets, kept under this one header
       when light, or split into their own `**Tests**` / `**Live**` headers
       when either is substantial:
         - **Tests** — local suite outcome (framework, counts, pass/fail).
         - **Live** — probing what is *actually serving* (not localhost): the
           ship propagated and responds correctly where it counts.
    3. **Review** — the quality gate: context-isolated review outcome (passed, or
       findings + how they were resolved). A review skipped by the check log
       names the pass that stood in (skill and time), and one `/rev` skipped
       as tiny names that and its reason. Otherwise omit if no review ran.
    4. **Pending** — the residue, LAST: dormant-until-configured, deferred items,
       known issues / failures, flaky tests, follow-ups, and **every developer-checklist item the
       user has not yet confirmed** — checkables prefixed `[chk]` and keeping their
       row's action + expected result, IN THE WIDGET'S ORDER (that order is the
       checks' IDs), so the next dep REBUILDS the table instead of guessing which
       residue bullets were checkables. A PARTIAL dep also records
       `[stamp-hold <sha>]` here (see Change-Gate) so the completing dep can stamp
       from the file. This section is what the NEXT dep reads to
       rebuild its cumulative checklist (see Dep Report), so an item omitted here is
       an item forgotten. Omitted entirely when genuinely clean.
  A bullet is a terse one-liner; add an **indented continuation line** beneath it
  ONLY when the one-liner isn't self-evident — not on every bullet. This grouped
  shape intentionally diverges from the flat chatlog bullet list — deploy results
  are categorical, so grouping them reads far faster.
- **Project-scoped**: only *this* repo's dep — never log another project's or
  off-project work.
- **Secret-redaction (mandatory)**: never write literal secret values (API keys,
  JWTs, tokens, passwords, DB creds, PEM blocks) or PII into a bullet. Describe
  intent, not value; when in doubt, redact.
