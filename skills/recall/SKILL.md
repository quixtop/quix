---
name: recall
author: shrix
description: (shrix) >
  (shrix) Look up EARLIER Claude Code sessions for this project — the ones a
  /clear or a new window left behind. Answers "what did we do before the
  clear", "which session had X", "what was I working on yesterday". Reads the
  raw JSONL transcript store; never edits it. Triggers on /recall, /recall <term>,
  "the previous session", "before the clear", "search my sessions for X".
  NOT for the current conversation (use /pendings) and NOT for carrying state
  forward (use /handoff).
---

# /recall — reach back into earlier sessions

Claude Code writes one JSONL transcript per session under
`~/.claude/projects/<mangled-cwd>/`. A `/clear` starts a **new** session file
and leaves the old one fully intact, but nothing links the two: there is no
predecessor pointer, and the session title is a mutable label that sessions
reuse. So earlier sessions are reachable only by an explicit lookup — this one.

## The script does the scanning

```
~/.agents/skills/recall/scripts/recall-scan.py
```

| invocation | does |
|---|---|
| (no args) | 5 most recent real sessions for the cwd's project |
| `-n 10` | show 10 instead |
| `-s "term"` | only sessions whose text contains term |
| `--all` | every project, not just this one |
| `--show <id>` | dump one session's user prompts (last 40) |
| `--show <id> --full` | include assistant replies too |
| `--show <id> --tail 0` | every prompt, no limit |
| `--exclude <id>` | omit a session |

## Why the filter is the whole point

**Almost every transcript is agent scratch, not conversation.** In one real
project the store held 491 transcripts of which only 6 were actual sessions;
the other 485 were hook classifiers, chapter markers and gate checks, each a
single boilerplate prompt. A naive listing returns nothing but noise.

The cut is **structural** — at least `--min-prompts` real user prompts
(default 3) — never a blacklist of known boilerplate, so it stays correct as
new agent types appear. Injected turns (those starting with `<`) never count.

## Running it

1. **Always exclude the current session.** Its transcript is the newest file
   and will otherwise top the list. Get the id from `get_session("self")` on
   Desktop, or recognise it as the row whose latest prompt is the live one,
   then pass `--exclude <id>`.
2. **List before dumping.** Run bare (or with `-s`) first, pick the session,
   then `--show` it. A large session holds thousands of prompts.
3. **`--tail` guards context**, defaulting to the last 40 prompts. Raise it
   deliberately; `--tail 0` on a 1489-prompt session emits ~3 MB.
4. **Search by content, not by name.** Titles change within a session and
   repeat across sessions, so `-s "cc-xtn"` beats "the Scripts one".
5. **State the scope you searched** — window and project — before reporting.
   Never silently narrow "all my sessions" to the newest five; if the honest
   answer needs `--all` or a bigger `-n`, run it.

## Reporting back

Give a table of candidates — when · id · prompts · title — then **summarise**
in prose. Never paste the raw dump; that is what the context budget is being
spent to avoid. Quote a specific prompt only when the exact wording is the
answer.

For "where was I / what was I doing", answer in this order, not chronological
order. The reader wants the current state first and the history only if it
explains it.

1. **Capsule** — at most 5 lines: what the work is and where it stands.
2. **Threads** — one line each, every one carrying a status tag.
3. **Problems** — the recurring ones, including anything tried that did not
   hold, so the next attempt starts where the last one stopped.
4. **Next move** — the single most useful concrete action.

### Status tags — every thread gets exactly one
`[merged]` · `[open PR #N]` · `[in flight <branch>]` · `[done, uncommitted]`
· `[reverted]` · `[planned, not started]` · `[abandoned]`

An untagged thread reads as finished when it usually is not. If the
transcript does not say, the tag is `[unknown]` — never a guess.

### Tag from live state, not from the transcript
A transcript records what was *said*, sometimes months ago. Check before
tagging: `git branch --list`, `gh pr view <n> --json state`, or a plain `ls`.
A thread left "in flight" is frequently merged or gone by now.

Say plainly when nothing matched — a session never written to disk does not
exist, and searching harder does not invent it.

### No subagent fan-out — deliberate
The scanner already filters structurally and caps its output, so raw
transcripts never reach this context. Fan-out would be machinery for a solved
problem.
