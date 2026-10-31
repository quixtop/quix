---
name: ste100
author: shrix
description: "(shrix) Check a project's architecture docs against ASD-STE100 Simplified Technical English (Issue 9) and render docs/arch/ste100.html — a colour-coded drawing sheet of the project's STE compliance plus an STE overview — and the docs/arch.html hub with two tabs: System (archify's docs/arch/archify.html, the default) and STE100. Proposes STE rewrites, applied only on a yes. Use when asked to check or rewrite docs in STE / Simplified Technical English."
metadata:
  version: "1.0"
  category: documentation
---

# ste100 — Simplified Technical English for project docs

Checks the written prose of a project's docs against ASD-STE100 Issue 9, keeps a
per-project STE dictionary, and writes these files in `docs/`:

| file | what it is | edit by hand? |
|---|---|---|
| `arch.html` | the hub: two tabs top-right — **System** (archify, the default) and **STE100** | never — regenerate |
| `arch/ste100.html` | sheet 1: this project's STE sheet · sheet 2: STE overview · all findings | never — regenerate |
| `arch/ste100.json` | the source: project dictionary, worked rewrites, score history | yes — it is the source |
| `arch/archify.html` | archify's system picture (archify writes it, from `arch/archify.json`) | never — archify's |

Commit the JSON beside the HTML, so the dictionary and history survive. One HTML
file opens in any browser, needs no server, and reflows from phone to wide screen.

## Help

`/ste100 -h | --help | help` (sole argument): reply with one sentence on what it does,
the full `description:` above, and the invocations below. Do not run anything.

## Invocations

| invocation | does |
|---|---|
| `/ste100` | check the arch family of the current project, curate the JSON, render the sheet and hub |
| `/ste100 --all` | the same, plus the reqs and design families and the root README |
| `/ste100 <file>…` | check those files only and report; no sheet |
| `/ste100 --arch <file>…` | check and curate those files only, propose their rewrites, then render the whole sheet and hub (§ In an arch update) |
| `/ste100 rewrite <file>` | propose STE rewrites for one file, applied only on the user's yes |

Scope (the arch family): `ARCHITECTURE.md`, any `arch.md`, `docs/arch.md`, `docs/arch/**`.
`--all` adds `docs/reqs.md`, `docs/reqs/**`, `REQUIREMENTS.md`, `docs/requirements/**`,
`reqs-*.md`, `DESIGN.md`, `docs/design/**` and the root `README.md`.

## Safety gates

- **Never edit a doc without the user's yes for that file.** Rewrites are proposed as a
  diff per file; a yes for one file is not a yes for the next.
- **Never push.** Report what changed.
- **Never hand-edit `arch/ste100.html` or `arch.html`.** They are generated; change the
  JSON or the docs and run `render` again.
- **Never overwrite an `arch.html` that is not the ste100 hub.** The script refuses and
  says so; tell the user to move an old archify page to `docs/arch/archify.html` first.
- **Never reproduce the ASD-STE100 text or dictionary.** Restate rules in your own words;
  the standard is a free download from asd-ste100.org.
- Code, backticked names, paths, commands, tables and diagrams are never rewritten.

## Workflow

The script is `scripts/ste100.py` in this skill's folder (Python 3, standard library
only). Run it from the project root. Read `references/rules.md` before rewriting
anything: it is the full rule set in our words, with what the script checks and what
you must judge.

1. **Scope.** `python3 <skill>/scripts/ste100.py scope . [--all]` — no files means
   nothing to check: say so in one line and stop.
2. **Lint.** `python3 <skill>/scripts/ste100.py lint <files> --json --data docs/arch/ste100.json`.
   Read the findings. `fail` = a clear break of a rule; `check` = needs your judgement.
3. **Curate `docs/arch/ste100.json`** (create it when missing; shape below):
   - `dictionary` — each technical noun and technical verb the docs use, once: one
     meaning, an example, and `not`: the other names seen for the same item (1.11, 9.4).
     Add a term only when the docs really use it.
   - `anatomy` — the two or three worst sentences, each with an STE rewrite and 2–4
     `notes` naming the rule each change applies. The rewrite must keep the meaning
     exact and pass `lint` itself. Copy `original` from the doc verbatim: render marks
     the example stale when the source sentence changes.
   - `meta.project`, `meta.owner`, `meta.spelling` (`en-US` default, `en-GB` if the
     project says so), and optionally `meta.findings_per_rule`: list at most that many
     findings per rule on the sheet, fails before checks (0 or absent = all). Counts and score always
     cover every finding; use it when a big project makes the page heavy.
4. **Render.** `python3 <skill>/scripts/ste100.py render . [--all]` — writes the sheet,
   the hub, and today's score into `history` (one entry per day; a second run the same
   day replaces it). Its last line is the status: ✓ clean, ⚠ findings or hub skipped,
   ✗ failed.
5. **Rewrites.** For each file with fails, offer the rewrites as a diff, grouped by file.
   Apply only on a yes, then lint and render again.
6. **Report.** Score, fail and check counts, the top rules broken, the files written,
   and how to view it:

   ```bash
   open docs/arch.html
   ```

## In an arch update

A whole arch update — archify's system picture, this sheet and the hub — is
`/arch`'s; it runs `/ste100` as its prose step, only when arch prose was added or
rewritten. It runs `/ste100 --arch <files>` with the arch files the change touched: then steps 2, 3 and 5
cover only those files — lint them, curate only the dictionary terms and anatomy
examples they bring or change, and propose rewrites for them alone — while step 4
still renders the sheet for the whole family (a fast script, so the score stays
complete). When `/arch` itself was run by another skill, the rewrites are
only proposed — no per-file ask, nothing edited — and go back in the report.
`/arch --all` and a standalone run keep the default scope. Run
`/ste100` alone for an STE check or rewrites. The `hub` command
(`python3 <skill>/scripts/ste100.py hub .`) rebuilds just the hub, as `/arch` does
when only archify's page changed.

## `docs/arch/ste100.json`

```json
{
  "version": 1,
  "meta": {"project": "name", "owner": "who", "spelling": "en-US", "findings_per_rule": 25},
  "dictionary": [
    {"word": "worker", "pos": "n", "meaning": "a Cloudflare Worker script",
     "example": "The WORKER sends the reply.", "not": ["service", "lambda"]}
  ],
  "anatomy": [
    {"file": "docs/arch.md", "line": 12, "type": "descriptive",
     "original": "The token is refreshed by the worker every hour.",
     "ste": "The worker refreshes the token one time each hour.",
     "notes": [{"text": "refreshes", "note": "active voice, simple present", "tone": "ok"}]}
  ],
  "history": [{"date": "2026-10-05", "score": 82, "sentences": 140, "fails": 31, "checks": 12}]
}
```

`notes[].tone`: `ok` (approved change, green) · `fix` (red) · `term` (technical name,
purple) · `info` (blue). `history` is written by `render`; do not edit it.

## What the sheet shows

Sheet 1, this project: A doc tree with pass/fail per file · B worked rewrites · C verb
forms found · D project dictionary and words to replace · E measured limits (max and
p90 against 20/25 words, 6 sentences, 3-word nouns, 1 instruction) · F score trend ·
title block. Sheet 2: the STE overview (`references/overview.json`). Below both: every
finding, filterable by level and rule, each linked to its file and line. Colours carry
meaning: green approved, red not approved, amber check, purple technical name, blue
measured value, teal rule, grey file.
