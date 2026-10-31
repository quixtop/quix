---
name: pendings
author: shrix
description: "(shrix) End-of-session sweep of the CURRENT conversation for anything the user may have missed — unanswered questions, undecided choices, deferred work, unclaimed offers, warnings flagged in passing, checks still owed. Read-only; `topic:<words>` scopes it. Use before wrapping up, or on 'did I miss anything?' / 'what's still open?'."
metadata:
  version: "1.3"
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
FIRST casualties, which is why a compacted session is scanned from its raw
transcript (Step 0).

## Invocation

- `/pendings` — full report
- `/pendings <word>` — filter to matching categories (e.g. `questions`,
  `pending`, `offers`, `verify`)
- `/pendings topic:<words>` — only items about that one topic (§ Topic scope)
- `/pendings help` (or `-h`, `--help`) — print this skill's description and
  how to invoke it, then stop

## Hard Constraints

- **Full session, not just live context.** Sweep the ENTIRE session; after a
  compaction that means the raw transcript (Step 0) — the in-context summary
  is a guaranteed miss. `topic:` narrows what is classified, never what is
  searched (§ Topic scope).
- **Do the scan yourself; no subagent.** You are the only reader that sees both
  the live turns AND (via the transcript file) the compacted ones — a subagent
  sees neither reliably. Reading the on-disk transcript file yourself is
  expected; it is not a subagent dispatch.
- **Read-only.** Never act on, fix, or start a listed item, however trivial.
  The user opts in by replying with an item number.
- **Conversation only.** Scan what was actually said in THIS session — the
  transcript IS that record. Never invent items from system-prompt rules,
  CLAUDE.md, or task files (`/proj-tasks` and `/todo` own those).

## Scan Procedure

### Step 0 — Recover the full record FIRST (when compacted)

Detect compaction: a "This session is being continued… / Summary:" block, a
system-reminder pointing at a transcript path ("read the full transcript at:
<path>"), or any context-management note. If present, the in-context text is
LOSSY — recover the rest before you scan:

- **Find the transcript.** Usually the path is surfaced in a system-reminder.
  Otherwise it is `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, where
  `<cwd-slug>` is the cwd with every character that is not an ASCII letter or
  digit (`/`, `.`, accents) replaced by `-` — an emoji by `--` — and a slug
  over 200 characters cut and given a suffix (match its first 200).
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

### Topic scope (`topic:<words>`)

Search the whole record, but only to LOCATE the topic; classify inside it
alone:

- **Spans** — every chapter mark whose title matches the topic. A span runs
  from the last user prompt before that mark to the last user prompt before
  the next mark: the prompt that opened a topic comes before its mark. Match
  by meaning, not substring: a 40-character title rarely repeats the topic's
  exact words. Find marks by structure, never by grepping the text
  `Chapter marked: …` — rules and edits quoted into the transcript contain it
  and yield fake marks. In the raw `.jsonl`, a mark is a `tool_use` block in an
  assistant entry's `message.content` whose `name` ends in `mark_chapter`, its
  title at `input.title`; this lists them in order:
  `jq -r 'select(.type=="assistant")|.message.content[]?|select(.type=="tool_use" and (.name|endswith("mark_chapter")))|.input.title' <transcript>`.
  In live context, a mark is one of your own `mark_chapter` calls.
- **Plus** any other turn that names the topic's key terms.
- **Classify only those turns.** Resolution still counts wherever it happened:
  before listing an item, check the rest of the session for its answer.
- **Name the scope** in the heading: `## ⏳ pendings — <n> open item(s) ·
  topic: <words>`.
- **Nothing matches** — no span AND no key-term turn → output only
  `⚠️ No turns found for topic: <words> — check the topic name.` Never fall
  back to the whole session silently, and never print the clean-topic line
  (§ Output Contract): that one means the topic was found with nothing open.

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

A TABLE, not a prose list — compiled points default to tabular form.
One row per item, scannable at a glance:

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
- Width: keep each row within the per-row cap when one is injected,
  otherwise about 10 columns under the terminal width. If the four
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
- Topic-scoped (`topic:<words>`): append ` · topic: <words>` to the heading
  and to the nothing-found line, so a clean topic never reads as a clean
  session. A topic that was never found gets the ⚠️ line from § Topic scope
  instead.
- If the session was compacted, you were REQUIRED to recover items from the
  raw transcript (Step 0); append one line confirming it — e.g. "Scanned the
  full transcript, not just the in-context summary." Fall back to the weaker
  "covers only what survived summarization" caveat ONLY if the transcript was
  genuinely unreadable.
