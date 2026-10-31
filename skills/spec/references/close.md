# spec — Step 8, the Final Package
<!-- author: shrix -->

READ at Step 8, before printing the close.

The package opens with **Key points** — a digest of what the approved spec
decided, so the user sees the feature before the list of files.

- Take every row from the approved files only, never a new claim; the one
  judgement is the complexity rating, made from the plan's size.
- One line per cell. A cell that lists items holds up to three, separated by
  ` · `, most important first: must before should before could, else the
  order the file gives.
- An item shown in an earlier row is not repeated in a later one — the same
  fact in other words counts as the same item.
- Drop a row with nothing in it — except Prerequisites, which always shows,
  `none` included.

| row | taken from |
|---|---|
| Goal | 4.1 Feature Overview: the one-line summary and the problem it solves |
| Requirements | the simplest version (in Decided or Assumptions) and the key requirements and constraints filed to the reqs docs (To file · reqs) |
| Architecture | the chosen approach with the one-line reason it won (Assumptions, or Decided when it was a CRITICAL pick), the runner-up from Alternatives considered, if any, with why it lost, and the structural decisions filed to the arch docs and ADRs (To file · arch, ADRs) |
| Design | the look-and-feel and UX decisions filed to the design docs (To file · design) |
| Out of scope | 4.13 Out of Scope |
| Key decisions | Decided, the CRITICAL answers first |
| Risks / open | every review finding still open first — never cut to fit — then the first risks listed in 4.12, up to three items in all |
| Plan | a fixed form, not a list: phases (or `flat`) · tasks · the summed estimate · complexity (Simple / Medium / Complex); post-build: `none — built` |
| Prerequisites | Prerequisites |

Spec-only re-run: each row shows only what this re-run changed — its changed
Decided entries, its To file entries (a dropped decision marked `dropped`),
and changed lines in 4.12 and 4.13 — and a row with no change is dropped.
Plan shows the plan's own estimate, marked `unchanged`; Prerequisites shows
the current list.

```
📦 Final Package — <ready to build | spec updated | documented>: <feature>

**Key points**

| aspect | key point |
|---|---|
| Goal | <one line> |
| … | (the rows above, in that order) |

**Status**: approved <date> (spec-only: the plan keeps its own)
**Spec**: <root>/docs/spec/<feature>.md   **Plan**: [the plan's absolute path — `<root>/docs/plan/<feature>.md`, or where a re-run found it; post-build: none]
**Companions**: [absolute paths, "in the spec", or "none"]
**Filed**: reqs · arch · design · tasks · ADRs (as applied)
**Figures**: `/arch`'s report line — archify [updated / created / not needed / stale] · ste100 [run / hub only / not needed / stale] — or `arch: not needed`, or `figure: stale — <why>`
**Review**: [rounds] · [fixed] · [fixed after round 2, not re-reviewed] · [refuted] · [open: N — listed under Risks / open]
**[Committed as `<sha>` | Commit together | Keep together — not a git repo]**: the spec, plan and companions; the doc files and docs/adr/ entries Step 7 changed; archify.json with archify.html; ste100.json with its sheet and hub
```

## Related Skills

In the order `/spec` reaches them:

| Skill | Relationship |
|---|---|
| `superpowers:writing-plans` | writes the plan to `docs/plan/<feature>.md` (Step 4) |
| `arch` | the system figure, the STE check of new arch prose and the `docs/arch.html` hub (Step 7) |
| `dev` | builds it (offered at Step 8) |
| `/design` (built-in) | UI mockups, offered at Step 8 |
