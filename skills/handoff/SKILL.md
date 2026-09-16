---
name: handoff
author: shrix
description: "(shrix) Use when continuing this work in a fresh session that cannot inherit the current context — CLI to the Desktop app, a different agent on this machine, or another machine/the web app IF the project folder is synced there. Writes a disposable, self-deleting HANDOFF.md at the project root for a cold resume; `/handoff <hint>` puts that item first in Next Steps. Not for mirroring a live session you keep open — use Remote Control."
---

# Handoff

Write a single, disposable `HANDOFF.md` that lets a COLD session — one with no
access to this conversation — resume the work. The canonical case: moving from
the CLI to the Claude Desktop app, whose session runs in an isolated VM that
cannot read the CLI transcript or the host temp dir, and whose Remote Control
bridge dies the moment the CLI closes. A document inside the project folder
(which the Desktop VM mounts read-write when you open it) is the only bridge
that survives.

## When NOT to use

If you are keeping the CLI session open and just want to view/drive it from
Desktop or mobile, use Remote Control — it is a lossless live mirror. This
skill is for the case where the original session goes away.

## Steps

1. **Find the project root.** Run `git rev-parse --show-toplevel`. If it fails
   (not a git repo), use the current working directory.

2. **Gather context from THIS conversation** (the dialogue itself, not just
   what is on disk):
   - **Goal** — what we are trying to accomplish.
   - **Current Progress** — what is done so far.
   - **What Worked** — approaches that succeeded.
   - **What Didn't Work** — approaches that failed, so the next session does
     not retry them. This lives only in the conversation; capture it.
   - **Key Files Touched** — each path with a one-line reason.
   - **Artifacts** — reference PRs, commits, specs, and issues by path or URL.
     Do NOT paste their contents; link to them.
   - **Suggested Skills** — skills the next session should reach for.
   - **Next Steps** — ordered action items. If the user passed a focus hint
     after `/handoff`, put that first.
   **Redact as you gather** — do not collect API keys, tokens, passwords, or PII into your notes; see step 4.

3. **Resolve the origin line.** Record cwd, model, and today's date. Best-effort
   capture the CLI session id (omit if empty):
   ```bash
   h=$(pwd | sed 's/[/.]/-/g'); ls -t ~/.claude/projects/"$h"/*.jsonl 2>/dev/null | head -1 | xargs -I{} basename {} .jsonl
   ```
   An empty result is expected and fine (this is a best-effort lookup of Claude Code's internal project path) — just omit the CLI session id from the Origin line.

4. **Redact secrets.** Never write API keys, tokens, passwords, or PII into the
   doc. If unsure whether a value is sensitive, omit it.

5. **Write `<project-root>/HANDOFF.md`**, overwriting any existing copy, using
   the template below. Fill every section from step 2; drop a section only if
   it is genuinely empty. Do NOT touch `.gitignore`, and do NOT commit the file —
   it is transient and the consuming session deletes it (see the cleanup footer).

6. **Report to the user:**
   - the file path,
   - the folder to open in Claude Desktop (the project root),
   - the exact phrase to paste into the fresh session: `read HANDOFF.md and continue`,
   - a reminder not to commit `HANDOFF.md` (it self-deletes once the next session reads it — and if that session forgets to delete it, remove it yourself before your next commit).

## Template

```markdown
# Handoff — <topic>
> RESUMING? You are a fresh session continuing prior work.
> Read this file fully, then continue from "Next Steps" below.
> Origin: <cwd> · <model> · <date> · CLI session <id-or-omit>

## Goal
<one or two sentences>

## Current Progress
<what is done so far>

## What Worked
<approaches that succeeded>

## What Didn't Work
<approaches that failed — do not retry>

## Key Files Touched
- `path/to/file` — <one-line why>

## Artifacts
- <PR / commit / spec / issue — link or path, never pasted content>

## Suggested Skills
- <skill name> — <when to use it here>

## Next Steps
1. <ordered; focus hint first if one was provided>

---
> CLEANUP: Once you have read this and resumed work, delete this file
> (`rm HANDOFF.md`). It is a one-shot bootstrap, not a kept document.
```

## Notes

- One-shot and disposable. Overwrite on each invocation; never merge with a
  prior `HANDOFF.md`.
- The cleanup footer instructs the consuming session to delete the file once
  the work is absorbed. This is intentional and should always be included.
- Not git-ignored by design: it self-deletes, so a permanent `.gitignore` entry
  would outlive the file. Leave `.gitignore` untouched; just don't commit it.
