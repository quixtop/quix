---
name: arch
author: shrix
description: "(shrix) Bring a project's architecture pictures up to date in one step — archify's system picture (docs/arch/archify.html), the STE100 sheet (docs/arch/ste100.html, via /ste100) and the docs/arch.html hub that shows them as tabs — running only what the change needs. Use after an arch change, or on /arch, 'update the arch diagram', 'refresh arch.html'. NOT for writing arch prose (/spec) or STE rewrites alone (/ste100)."
metadata:
  version: "1.0"
  category: documentation
---

# arch — the architecture pictures, in one step

The arch family (`arch.md`, `docs/arch.md`, `docs/arch/**`, `ARCHITECTURE.md`,
per-module arch docs) is the single source: prose plus inline Mermaid per
area. Three pages are generated from it, and none is ever hand-edited:

| file | made by | what it is |
|---|---|---|
| `docs/arch.html` | `/ste100` (its `hub`) | the hub: two tabs — System (the default) and STE100 |
| `docs/arch/archify.html` | archify, from `docs/arch/archify.json` | ONE whole-system picture |
| `docs/arch/ste100.html` | `/ste100`, from `docs/arch/ste100.json` + the arch prose | the STE100 sheet |

`archify.html` is what users and newcomers are shown — interactive, themed,
far more legible than a fence — so a cramped or stale one is worse than none.
It is never the source of truth. archify is a third-party skill: `/arch` runs
it and never edits it.

| invocation | does |
|---|---|
| `/arch` | update what the current arch change needs |
| `/arch --all` | regenerate all three pages: the "only when" gates of steps 2–3 are skipped; `/ste100` keeps its default arch-family scope (never its own `--all`) |

## Steps

0. **Clear the way** — an old archify page sitting at `docs/arch.html` (not
   the ste100 hub) moves FIRST, on the user's yes: it to
   `docs/arch/archify.html`, its JSON to `docs/arch/archify.json`. Until it
   moves, the hub cannot be written.
1. **What changed** — the arch-family edits the caller or the user
   names, else the arch-family files this session changed (`git status`; in a
   folder that is not a git repo, the files this session edited). None and no
   `--all` → `arch: not needed`, and stop.
2. **System picture — archify**, only when the change shows in the
   whole-system view: edit `docs/arch/archify.json`, then run archify's
   `deliver` with the output `docs/arch/archify.html` (creating both when
   absent). It validates and opens the page at several viewport sizes, so
   announce it first. Planned parts carry `(planned)` in their tag and no
   source references, and in an architecture figure dashed connections
   (dataflow and sequence figures use dashes for async, so there the tag alone
   marks them) — never shown as live. A minor change that does not show there
   → `archify: not needed`.
3. **STE sheet — `/ste100`**, only when the change added or rewrote arch
   prose. Run `/ste100 --arch <the arch files step 1 found>`: it lints,
   curates and proposes rewrites for those files only, then renders the whole
   sheet AND the hub. On `/arch --all`, run plain `/ste100` (its default
   arch-family scope). Run directly, rewrites are applied only on a yes per
   file; run by another skill, it never asks — it stops after rendering and
   returns its rewrite proposals instead. No prose changed →
   `ste100: not needed`.
4. **Hub only** — step 2 created `archify.html` for the first time, step 3
   did not run, and `docs/arch.html` exists → `python3
   ~/.agents/skills/ste100/scripts/ste100.py hub .`. No hub yet → leave it;
   the first `/ste100` run creates it. Read the script's last status line: a
   `⚠` (hub skipped) is reported as `stale — <its reason>`, even though the
   script exits 0.
5. **Report**, one line —
   `archify [updated · created · not needed · stale — <why>] · ste100 [run · hub only · not needed · stale — <why>]`
   — and what to commit together: `archify.json` with `archify.html` (without
   the JSON every run re-authors the picture from scratch and it churns), and
   `ste100.json` with `ste100.html` and `arch.html`. A page nobody can open
   after cloning is pointless, so the HTML is committed too. Deferred → say
   which page is stale. Run by another skill, ste100's rewrite proposals
   follow the report line, word for word, for the user to take up later.

## Safety gates

- Never hand-edit a generated page: change its JSON or the prose, then
  regenerate.
- Never overwrite an `arch.html` that is not the ste100 hub (ste100 refuses);
  step 0 moves an old archify page out of the way first.
- Never push. A doc rewrite needs its own yes (ste100's gate).
- A step whose tool is missing or fails is reported `stale — <why>`; the
  other steps still run.
