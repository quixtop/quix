---
name: proj-tasks
author: shrix
description: "(shrix) One-line glance at the PROJECT task files (the tasks family: TODO.md, docs/tasks.md, docs/tasks/…) with priorities — read-only. `/proj-tasks -f` adds the project status view: completion and active tasks, recent pushes, uncommitted and unpushed work, smoke-check state of what shipped, system health (tests, build, docs, CI, dependencies) and the next step. Use when checking pending project tasks, prioritizing next work, session planning, or asking for the project's status. NOT the personal todo manager — use /todo."
metadata:
  version: "1.2"
  category: status
effort: low
---

# Task Status Glance

Quick task glance: open items listed, done ones counted.

```
/proj-tasks                      the glance below
/proj-tasks -f | --full | status the glance plus the project status view — READ references/full.md first
```

## Auto-Detection

Read the whole tasks family — every one of these that exists, never just the
first:
- `docs/proj/tasks.md`
- `docs/tasks.md`, `docs/tasks/**/*.md`
- `TODO.md`, `TASKS.md`, `tasks.md`

**If no tasks file found**: Say "No tasks file found. Create `docs/tasks.md` to track tasks."

---

## Instructions

1. Auto-detect project name from git or directory
2. Read every tasks-family file found
3. Extract task names, priorities, and status
4. Print the glance (Output Format)

**Expected task-line format** (what step 3 parses): a markdown checkbox with a
priority token — `- [ ] P1: Task name — optional/file.ts`; `- [x]` marks done.
Lines without a `P0`/`P1`/`P2` token default to P2; anything unparseable falls
into the malformed-entry handling below.

**Section format** — files with no checkboxes, where each `##` heading is one
owed item (done items are removed, not ticked, so there is nothing to count as
done). Parse it this way:
- Each `##` heading is one item; its name is the heading, cut to ~80 chars. A
  heading that only groups items ("Owed from the … audit") counts its
  bold-led bullets (`- **…**`) as the items instead, named by their bold text.
- Priority: a `P0`/`P1`/`P2` token wins; else ⭐, `TOP`, 🔴 or `URGENT` → P0;
  else P2. A ✋ in the heading means the item waits on the owner — keep its ✋
  in the line.
- The header reads `📋 **Tasks** (N open[, M need you])` — no done count.

---

## Output Format

Header line with counts, then OPEN tasks one line each, P0 → P1 → P2 (done
tasks are only counted). At most 10 lines: past 9 open tasks, show 8 and end
with `… +M more`. No descriptions, no explanations.

```
📋 **Tasks** (X active, Y pending, Z done[, N malformed skipped])
🔴 P0: [task name] — [file]
🟡 P1: [task name] — [file]
⏳ P2: [task name] — [file]
… +M more
```

Emoji is keyed to priority: 🔴 P0 (urgent), 🟡 P1 (active), ⏳ P2 (later/pending).

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
| Malformed entry | Tasks missing status, or inconsistent formatting | Skip it; the header counts it (`N malformed skipped`) |
| Empty file | File created but no tasks added yet | Show "No tasks yet" with a starter template for the first task entry |
| Permission error | File exists but not readable | Report the permission issue and suggest `chmod` or checking file ownership |
| Several family files | e.g. `TODO.md` and `docs/tasks/*.md` both exist | Merge them into one glance; counts cover all of them |

