---
name: pendings
author: shrix
description: "(shrix) End-of-session sweep of the CURRENT conversation for anything the user may have missed — unanswered questions, undecided choices, pending/deferred work, unclaimed offers, warnings flagged in passing, manual checks still owed. Read-only; reads the raw transcript when compacted. Use before wrapping up or /handoff, or on 'did I miss anything?' / 'what's still open?'."
metadata:
  version: "1.1"
  category: status
---

# pendings — What Slipped Past You

Long sessions bury things: Claude asks a question, offers a follow-up, flags a
risk, leaves a verification checklist — and the user scrolls past. `/pendings`
re-reads the whole session and lists everything still waiting on the
user, prioritized.

**Core principle: only OPEN items.** Anything later answered, done, or
superseded is EXCLUDED. One resolved item in the list teaches the user to
skim the report — which recreates the original problem.

**Compaction is the worst offender.** Once a long session is summarized, the
granular items — one-line offers, minor tweaks, micro-decisions — are the
FIRST casualties. A scan of the live context alone therefore silently drops
exactly what this skill exists to catch. When the session has been compacted,
the **raw transcript on disk is the source of truth**, not the in-context
summary — see Scan Procedure Step 0.

## Invocation

- `/pendings` — full report
- `/pendings <word>` — filter to matching categories (e.g. `questions`,
  `pending`, `offers`, `verify`)
- `/pendings help` — handled by the generic shrix self-help rule

## Hard Constraints

- **Full session, not just live context.** The record you must sweep is the
  ENTIRE session. After a compaction your live context holds only a lossy
  summary of the early turns, so when the session was compacted you MUST read
  the raw transcript from disk (Step 0) and scan that. Treating the in-context
  summary as complete is a guaranteed miss.
- **Do the scan yourself; no subagent.** You are the only reader that sees both
  the live turns AND (via the transcript file) the compacted ones — a subagent
  sees neither reliably. Reading the on-disk transcript file yourself is
  expected; it is not a subagent dispatch.
- **Read-only.** Never act on, fix, or start a listed item, however trivial.
  The user opts in by replying with an item number.
- **Conversation only.** Scan what was actually said in THIS session — the
  transcript IS that record. Never invent items from system-prompt rules,
  CLAUDE.md, or task files (`/tasks` and `/todo` own those).

## Scan Procedure

### Step 0 — Recover the full record FIRST (when compacted)

Detect compaction: a "This session is being continued… / Summary:" block, a
system-reminder pointing at a transcript path ("read the full transcript at:
<path>"), or any context-management note. If present, the in-context text is
LOSSY — recover the rest before you scan:

- **Find the transcript.** Usually the path is surfaced in a system-reminder.
  Otherwise it is `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, where
  `<cwd-slug>` is the working directory with every `/` replaced by `-` (leading
  `-` kept).
- **Read it efficiently.** If it is large, don't load it blind — grep for
  open-item signals: assistant turns containing `?`, and phrasings like
  "want me to", "should I", "your call", "I'd suggest", "we could", "offer",
  "later", "v2", "defer", "TODO", "verify", "smoke"; plus user turns that asked
  for something. Then widen to a full read of any region where those hits
  cluster.
- **Scan the UNION.** Merge what you recover from the transcript with your live
  context, then run the lifecycle test below over the combined set. An item
  raised pre-compaction and never resolved post-compaction is STILL OPEN — the
  summary dropping it is NOT resolution.
- **Only if unreadable** (transcript missing/inaccessible) do you fall back to
  the summary and flag the weaker survival caveat.

### Step 1 — Walk and classify

Walk the session start → end (recovered transcript + live turns).
For each candidate, track its lifecycle: raised → later addressed /
superseded / still open. Report only still-open items. Scan both directions:

- **Claude → user**: things Claude surfaced that the user never engaged with
- **User → Claude**: things the USER asked for that were never delivered —
  list these FIRST; they are Claude's misses, not the user's

### Categories

| # | Category | What to hunt for |
|---|----------|------------------|
| 1 | 🙋 Unanswered questions | direct questions (inline or AskUserQuestion) the user never answered; clarifications requested, then the topic moved on |
| 2 | ⚖️ Undecided choices | options/alternatives presented with no pick; recommendations neither accepted nor rejected; unilateral assumptions worth confirming |
| 3 | 🚧 Pending & deferred work | features agreed or requested but not started; "later"/"v2"/"after this" deferrals; plan steps never executed; partial implementations; open TodoWrite items |
| 4 | 🤝 Unclaimed offers | follow-ups, adjacent improvements, or amplifiers offered once — never accepted or declined |
| 5 | ⚠️ Flagged, not handled | warnings and risks mentioned in passing; review nits left "for the user to decide"; failing or skipped tests reported; errors surfaced but not resolved |
| 6 | 🧪 Verification owed | things Claude could not verify and asked the user to check (developer checklists, UI flows, extension reloads) with no confirmation since |
| 7 | 🧵 Loose ends | background tasks/subagents whose results were never discussed; files created but never used; work started then silently abandoned |

## Output Contract

A TABLE, not a prose list — compiled points default to tabular form
(`communication.md` § Tables). One row per item, scannable at a glance:

```
## ⏳ pendings — <n> open item(s)

| # | ! | item | next |
|---|---|------|------|
| 1 | 🔴 | **<crisp title>** — <why it matters, one line> | <concrete action> |
| 2 | 🟡 | ... | ... |
| 3 | 🔵 | ... | ... |
```

- `#` is the handle the user replies with ("do 3", "3, 5") — always present.
- `!` carries the priority icon; rows stay sorted 🔴 → 🟡 → 🔵 so the section
  headings are unnecessary.
- Keep `item` to a title plus one clause, and `next` to an imperative. If a
  row needs more, it belongs in a sentence BELOW the table, not inside it.
- Width: obey the injected per-row cap (`communication.md`). If the four
  columns won't fit, drop `next` into the `item` cell rather than wrapping.

- Priority mapping: 🔴 = awaiting a decision or blocking (cats 1, 2, and
  blocking 5) — undelivered user requests always lead this section;
  🟡 = agreed/likely work not started (cats 3, 4);
  🔵 = informational or verification (cats 6, 7, non-blocking 5).
- Number rows continuously down the table so the user can reply
  "do 3" or "3, 5".
- Rewrite each item crisply — never quote the original wording verbatim.
- Fold the WHERE into the `item` cell as a few-word anchor ("during the auth
  refactor"), never a quote — it earns its space only when the title alone
  would not locate the item.
- Dedup: an item raised twice is ONE entry.
- Unsure whether something was resolved? Include it, marked
  _(possibly addressed)_ — a false open beats a silent drop.
- Nothing found: output only
  `✅ Nothing outstanding — everything raised was addressed.`
- If the session was compacted, you were REQUIRED to recover items from the
  raw transcript (Step 0); append one line confirming it — e.g. "Scanned the
  full transcript, not just the in-context summary." Fall back to the weaker
  "covers only what survived summarization" caveat ONLY if the transcript was
  genuinely unreadable.
