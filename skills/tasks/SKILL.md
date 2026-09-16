---
name: tasks
author: shrix
description: "(shrix) Quick one-line glance at the PROJECT task file (TODO.md / docs/tasks.md) with priorities — read-only, never edits. Use when checking pending project tasks, prioritizing next work, or session planning. NOT the personal todo manager — use /todo for personal todos."
metadata:
  version: "1.1"
  category: status
effort: low
---

# Task Status Glance

Quick one-line task status showing active, pending, and completed items.

## Auto-Detection

Find tasks file (first found):
- `docs/proj/tasks.md`
- `docs/tasks.md`
- `TODO.md`
- `TASKS.md`

**If no tasks file found**: Say "No tasks file found. Create `TODO.md` or `docs/tasks.md` to track tasks."

---

## Instructions

1. Auto-detect project name from git or directory
2. Find and read tasks file
3. Extract task names, priorities, and status
4. Show ONE LINE per task with a priority emoji

**Expected task-line format** (what step 3 parses): a markdown checkbox with a
priority token — `- [ ] P1: Task name — optional/file.ts`; `- [x]` marks done.
Lines without a `P0`/`P1`/`P2` token default to P2; anything unparseable falls
into the malformed-entry handling below.

---

## Output Format

One header line with counts, then one line per OPEN task, priority-led. Done
tasks are only counted in the header, never listed.

```
📋 **Tasks** (X active, Y pending, Z done)
🔴 P0: [task name] — [file]
🟡 P1: [task name] — [file]
⏳ P2: [task name] — [file]
```

Emoji is keyed to priority: 🔴 P0 (urgent), 🟡 P1 (active), ⏳ P2 (later/pending).

**IMPORTANT**: Keep output under 10 lines total. No descriptions, no explanations.

---

## Example Output

📋 **Tasks** (3 active, 2 pending, 8 done)
🔴 P0: Fix payment webhook timeout — payments.ts
🟡 P1: Add email verification flow — auth/verify.ts
🟡 P1: Update API docs for v2 endpoints — docs/api.md
⏳ P2: Migrate to Node 22 — package.json
⏳ P2: Add dark mode toggle — theme.tsx

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No tasks file found | Project hasn't set up task tracking | Create `TODO.md` or `docs/tasks.md`; check alternate locations (`TASKS.md`, `docs/proj/tasks.md`) |
| Malformed entry | Tasks missing priority, status, or inconsistent formatting | Show warning, display parseable tasks, skip malformed ones with notice |
| Empty file | File created but no tasks added yet | Show "No tasks yet" with a starter template for the first task entry |
| Permission error | File exists but not readable | Report the permission issue and suggest `chmod` or checking file ownership |
| Multiple sources found | Both `TODO.md` and `docs/tasks.md` exist | Use the first match per priority order; mention other sources found so user can consolidate |

