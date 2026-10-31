---
name: handoff
author: shrix
description: "(shrix) Move work to any fresh session that cannot inherit this context — a new session on this machine (CLI, Desktop, IDE), a Projects thread, another agent or machine. Writes a self-deleting HANDOFF.md (`/handoff <topic>` scopes it to that topic), recovers compacted turns, and cold-read-tests it. NOT for mirroring a live session you keep open — use Remote Control."
---

# Handoff

Write one disposable handoff file that lets a COLD session — one with no access
to this conversation — resume the work. A file inside the project folder is the
bridge: any session that opens the folder can read it — a new CLI, Desktop or
IDE session, a Projects local thread — and one that can't (a cloud thread,
another machine) receives it uploaded or synced.

## When NOT to use

- **Keeping this session open** and driving it from the phone or claude.ai →
  Remote Control, a lossless live mirror.
- **Moving this whole session into the Desktop app** on the same machine →
  Desktop's `/resume` picks up a CLI session with its full conversation.
- **Moving this whole session into a cloud session** → Desktop's
  **Continue in › Claude Code on the Web** (needs git and a clean tree).

This skill is for when the WORK moves to a fresh session and this one goes away.

## Arguments

- `/handoff` → `HANDOFF.md`, covering the session's work.
- `/handoff <topic>` → `HANDOFF-<topic-slug>.md`, scoped to that topic end to
  end: every section covers only that topic, and its own step leads Next Steps.
  `<topic-slug>` is the topic lowercased, spaces as `-`, at most ~30 characters.

A session that spans several unrelated topics (several chapter marks, a subject
pivot) with no topic given: list the topics and ask which to hand off (step 4).
One file per topic — never one file blending them.

## Steps

1. **Find the project root.** Run `git rev-parse --show-toplevel`. If it fails
   (not a git repo), use the current working directory.

2. **Find this session's transcript.** Make up a random marker
   (`hnonce-` + 10 hex characters) and run ONE command containing it. The
   command is written into this session's transcript before it runs, so the
   grep matches this session and no other:
   ```bash
   find ~/.claude/projects -maxdepth 2 -name '*.jsonl' -mmin -10 -exec grep -l '<marker>' {} + 2>/dev/null
   ```
   Exactly one path → that is the transcript, and its basename is the session
   id. Zero or several → omit the id and the transcript from Origin; never
   guess.

3. **Recover the full record if compacted.** Detect compaction as `/pendings`
   Step 0 does: a "This session is being continued… / Summary:" block, or a
   notice naming the transcript path. The in-context text is then LOSSY — read
   the raw transcript (the notice's path, else step 2's) and gather from the
   union of transcript and live context. What was decided, tried or deferred
   before the compaction still counts; the summary dropping it is not
   resolution.

4. **Settle the scope, then pick the target file.** No topic was given and
   the session spans several unrelated topics (§ Arguments) → list them now,
   from the full record step 3 recovered, and ask which to hand off before
   going further. Then the target is `HANDOFF.md`, or
   `HANDOFF-<topic-slug>.md` (§ Arguments). If it already exists, the
   session it was written for has not read it yet, since the reader deletes
   it. Show its heading and Origin line and ask before replacing it. Never
   merge two handoffs.

5. **Gather** — from step 3's union, or the live conversation when nothing was
   compacted:
   - **Goal** — what we are trying to accomplish.
   - **Decisions** — what the user settled, with the reason, and every
     constraint they set ("don't touch X"). The next session must not reopen
     these.
   - **Current Progress** — one row per item with a status: ✅ verified (output
     seen this session) · 🟡 done but unverified, or pending · 🔴 blocked ·
     ✋ needs the user.
   - **What Worked** — approaches that succeeded.
   - **What Didn't Work** — approaches that failed, so the next session does
     not retry them. This lives only in the conversation; capture it.
   - **Open Items** — invoke `/pendings` (read-only), as
     `/pendings topic:<topic>` when a topic was given, and carry its open rows
     here: unanswered questions, un-executed approvals, deferred work,
     unverified claims. `/pendings` owns that sweep; do not re-implement it.
   - **State** — what lives outside the conversation and outside git: the
     branch and uncommitted changes; backups and files in this session's
     scratchpad or temp dirs (copy into the project anything the next session
     needs, or record that it will be gone); edits outside the project tree
     (`~/.claude`, `~/.agents`, other repos); background processes this
     session started and whether they still run.
   - **Key Files Touched** — each path with a one-line reason.
   - **Kept Records** — step 6.
   - **Artifacts** — PRs, commits, specs and issues by path or URL. Link them;
     never paste their contents.
   - **Suggested Skills** — skills the next session should reach for.
   - **Next Steps** — ordered action items; the topic's own step first. Each
     names who does it: the user (UI, logins, decisions) or the next session.
     A step that decides go/no-go comes BEFORE the steps it gates, names its
     check, and says what to do on a fail — stop, or how to undo what was
     already done.

   **Write for a reader who has nothing else.** Absolute paths only — never
   relative, never `scratchpad/…`. Expand every project-specific name and
   acronym on first use (an internal tool's name, a decision ID), and point to where
   the reader can look it up.

   **Redact as you gather** — never collect API keys, tokens, passwords or PII
   into your notes; see step 7.

6. **Put lasting findings in a kept file first.** The handoff deletes itself
   once read, so it must never be the only copy of anything worth keeping.
   Requirements, architecture and design decisions, and todos go to the
   project's capture docs — the reqs, arch, design and tasks families, each
   every related file (e.g. `docs/reqs.md` and `docs/reqs/**`), into the
   member whose topic fits — as current-state
   entries superseded in place (arch entries carry the one-line why);
   one-off session instructions and off-project items are not captured. Other
   lasting findings — research results, measurements — go into an existing
   project doc; when none fits, ask the user where. List each under Kept
   Records.

7. **Redact secrets.** Never write API keys, tokens, passwords or PII into the
   file. If unsure whether a value is sensitive, omit it.

8. **Write the file** at the project root from the template below. Fill every
   section; drop one only if it is genuinely empty. Do NOT touch `.gitignore`,
   and do NOT commit the file.

9. **Cold-read test.** Dispatch a fresh subagent, read-only and with no access
   to this conversation, giving it only the file's path. Ask it for: the goal;
   the first Next Step and how it would begin; each go/no-go check and what
   counts as a pass or a fail; what it must not retry; what is still open;
   what it must not reopen. Compare its answers with the session, fix every
   gap in the file, then test once more. Two rounds at most — report anything
   still unresolved. One exception: a gap that would make a go/no-go check
   pass or fail wrongly is fixed whatever the round, without a third test,
   and reported as untested.

10. **Report** — the file path, the cold-read outcome (gaps left unresolved,
    and any go/no-go fix made after the last round), the steps for the
    destination the user named (ask if none was named), and a reminder not to
    commit the file: it deletes
    itself once read, and if the next session forgets, remove it before your
    next commit.

    | destination | how the next session picks it up |
    |---|---|
    | a new session on this machine (CLI, Desktop, IDE) | start it in the project root; send `read <file> and continue` |
    | Projects local thread | **+ › Work locally**, send `Read <root>/<file> fully, follow its Next Steps, then delete it as it says`, then **Allow once** on that folder |
    | Projects cloud thread, or a cloud session | upload the file to the project's files — never commit it. Cloud threads load nothing from `~/.claude`, so the Decisions section is their only copy of your constraints |
    | another agent or machine | sync the folder there first, then as for a new session |

## Template

```markdown
# Handoff — <topic>
> RESUMING? You are a fresh session continuing prior work.
> Read this file fully, then continue from "Next Steps" below.
> Origin: <cwd> · <model> · <date> · session <id-or-omit>
> Transcript (same machine only): <path-or-omit>

## Goal
<one or two sentences>

## Decisions — do not reopen
- <decision> — <why, and who settled it>

## Current Progress
| # | item | status |
|---|---|---|
| 1 | <item> | <✅ · 🟡 · 🔴 · ✋> |

Status: ✅ verified · 🟡 unverified or pending · 🔴 blocked · ✋ needs the user

## What Worked
<approaches that succeeded>

## What Didn't Work
<approaches that failed — do not retry>

## Open Items
- <from /pendings: question, approval, deferred work, unverified claim>

## State
- Branch / uncommitted: <…>
- Outside the project: <edits in ~/.claude, ~/.agents, other repos; backups>
- Still running: <processes, or "nothing">

## Key Files Touched
- `path/to/file` — <one-line why>

## Kept Records
- `path` — <the lasting finding it holds>

## Artifacts
- <PR / commit / spec / issue — link or path, never pasted content>

## Suggested Skills
- <skill name> — <when to use it here>

## Next Steps
1. <who> — <action>; the topic's own step first
2. <who> — <go/no-go check> — on a fail: <stop, or how to undo>

---
> CLEANUP: Once you have read this and resumed work, delete this file if it is
> in your working tree (`rm <file>`). It is a one-shot bootstrap, not a kept
> record — anything lasting is listed under Kept Records.
```

## Notes

- One-shot and disposable. Never merge two handoffs; replace an unread one only
  after the user says so (step 4).
- The cleanup footer instructs the reader to delete the file once the work is
  absorbed. Always include it.
- Not git-ignored by design: it self-deletes, so a permanent `.gitignore` entry
  would outlive the file. Leave `.gitignore` untouched; just don't commit it.
- Never identify the session by the newest `.jsonl`: sessions share a folder,
  and `ls` may be a shell function that ignores `-t`.
