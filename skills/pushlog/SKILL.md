---
name: pushlog
author: shrix
description: "(shrix) Generate a pushlog entry documenting git changes — deterministic bash script computes paths/timestamp/diff range, LLM summarizes the filtered diff into bullets, secret-verifier gates the result. Runs the chatlog skill first. Use when logging git changes before a push."
metadata:
  version: "2.1"
  category: documentation
  dependencies:
    - chatlog
---

# Pushlog Generator

Generates a timestamped pushlog entry documenting git changes. Thin wrapper around `scripts/pushlog.sh` which handles all format and git-state logic deterministically. The LLM's only job is summarizing the filtered diff into bullets.

## Flow (must run in this exact order)

1. **Invoke the `chatlog` skill first** (via Skill tool — use the plain name `chatlog`; the backing dir is `chatlog`). Writes the session entry to `chatlog.md`; must exist and be current before pushlog.sh runs.
2. **Run `bash ~/.agents/skills/pushlog/scripts/pushlog.sh`** (via Bash). Emits a structured stdout blob (paths, timestamp, diff range, format instructions).
3. **Read the blob, summarize the diff into bullets**, prepend the entry to the pushlog file shown in the blob. Use `Edit`: `old_string` = header block (title + underline + blank line); `new_string` = header block + new entry + `---` separator.

**Critical**: never reverse step 1 and step 2. Running pushlog.sh before chatlog means chatlog.md won't reflect the current session. Meta-file filtering (see below) ensures chatlog.md's own write is excluded from pushlog bullets, so the ordering is safe.

**Project scope**: pushlog is inherently scoped to *this* repo — `git diff` only sees changes inside the repo tree, so off-project edits (dotfiles, `~/.claude/`, other repos) never reach the bullets by construction. Your job is to summarize that diff, **not** the conversation: don't pull in off-project tangents discussed during the session. (`chatlog` applies the matching path + topic filter on the conversation side.)

## What the script handles automatically

- **First-run setup** — if pushlog.md has no entries, creates both `docs/logs/pushlog.md` and `docs/logs/chatlog.md` with correct headers, then exits. Run again after changes.
- **Diff range detection** — prefers `@{u}..HEAD` (commits ahead of upstream), falls back to `git diff HEAD` (working tree), aborts cleanly with "nothing to log" if both are empty.
- **Initial-commit scenario** — on the repo's first commit, emits a preformatted collapsed entry (`- initial project scaffold (N files, M lines)`) instead of a 30-bullet dump.
- **Meta-file exclusion** — removes `pushlog.md`, `chatlog.md`, `CHANGELOG.md`, and variants from the changed-files list so they can never appear in bullets.
- **Timestamp formatting** — deterministic `DDMonYY / H.MMp` format (e.g. `08Apr26 / 11.47a`) via `date` + `tr -s ' '` + `sed`.
- **Large-entry footer** — appends `- net change: N files, +A −B lines` for diffs touching 10+ files. Derived from `git diff --shortstat`.
- **Project name normalization** — for first-run headers, prefers `git remote origin` basename, strips version suffixes (`-v2`), replaces `-`/`_` with space, titlecases first char.
- **Legacy `•` self-heal** — rewrites legacy `• ` (U+2022) bullet markers to `- ` in both files. Markers only; `•` inside bullet text is untouched. Idempotent. Migrated lines stage with your next `git add`; stderr emits `📋 One-time bullet migration: …` with a count.

## What the LLM does (LLM-side)

After chatlog has run and pushlog.sh has emitted its blob, the LLM has five tasks:

1. Parse the blob to extract `PUSHLOG_FILE`, `TIMESTAMP`, `DIFF_RANGE`, `CHANGED_FILES`, `NET_CHANGE_FOOTER` (if present), and `MODE`.
2. If `MODE=initial_commit`, write the preformatted entry from the blob verbatim — do not generate additional bullets.
3. If `MODE=normal`, optionally run `git diff <DIFF_RANGE> -- <file>` on specific files for per-file context.
4. Summarize the changes into bullets following these format rules (no artificial limits):
   - Character: `- ` (markdown list marker — see anti-pattern at end of file for why not `•`/`*`/`+`)
   - Tone: **crisp and complete — cover every material change, but no padding, narration, or restating what the cited file paths/symbols already convey**. Length follows from scope: a one-line rename gets one line; a multi-file refactor earns more. Long is permitted when earned, never as a default.
   - File refs: backticks, `:line-line` ranges, comma-separated for multiple ranges per file
   - Group related changes into one bullet where possible
   - Include `NET_CHANGE_FOOTER` as the last bullet if the blob provides one
5. Compose the title as `**phrase; phrase; phrase**` — lowercase prose, 2–4 phrases separated by `; `, ordered by importance (fix > feat > refactor > docs). **Keep acronyms and proper nouns capitalized** so readers can identify them at a glance — `PRD`, `OAuth`, `API`, `CLI`, `JSON`, `URL`, `XSS`, `SDK` and the like, plus product and brand names (`OpenAI`, `macOS`, `YouTube`, `Postgres`, `TypeScript`, `Cloudflare`). The lowercase rule applies to prose words (verbs, common nouns, adjectives) — not to abbreviations or proper nouns. File-name fragments matching actual filenames stay lowercase (e.g., `arch`, `func`, `spec` referencing `arch.md` / `func.md` / `spec.md`).
   - Phrase budget: each phrase ≤ ~8 words / ~50 chars; full title fits on one line (target ≤ ~120 chars, hard ceiling ~150). Over budget → split or drop, never narrate.
   - Each phrase names an outcome or area of change, not its mechanism. Bullets carry mechanism, file paths, symbol names, counts, milestone IDs, phase markers, and `✓` receipts. The title never does.
   - One concept per phrase. If you reach for `+`, `with`, `via`, or `/` to join two ideas inside a phrase, that's a second phrase — and if that pushes past 4, the least load-bearing change drops out of the title entirely (it still appears in bullets).

   Prepend to `PUSHLOG_FILE` directly after the header block via `Edit`.
6. **Run the secret-pattern verifier** — execute `bash ~/.agents/skills/pushlog/scripts/pushlog.sh --verify`. This greps the topmost entry of `pushlog.md` (bounded by the `---` separator) and the full `chatlog.md` (which has no separators) for known secret shapes (API keys, JWTs, PEM blocks, Bearer tokens, AWS/Google/GitHub/Slack token prefixes). If it exits non-zero, **stop**, surface the warning, and edit the leaking bullet to remove the secret before continuing. Do not proceed to step 7 with a non-zero verify result. If the warning indicates the match is in chatlog and you can't find it in the bullets you just wrote, check older entries — the chatlog scan covers the whole file.
7. **Display the push command** — after writing the entry, extract the title text from between `**...**` (excluding the `[timestamp]`) and display it as the final output, in a ` ```bash `-tagged fence (the tag is what gives it a Run button — running it IS the intended next step here):
   ```bash
   push "the title text from the pushlog entry"
   ```
   Example: if the entry title is `**race category detection; speed-ctrl simplification** [09Apr26 / 6.43p]`, output:
   ```bash
   push "race category detection; speed-ctrl simplification"
   ```
   This is the LAST thing pushlog outputs. It feeds directly into `/push`'s commit message resolution (step 3 looks for `push "..."` in conversation context).
   **Important**: use the **pushlog** entry title only — NOT the chatlog session title from step 1. The chatlog title (written by chatlog earlier in the flow) describes the conversation narrative; the pushlog title describes the code changes. The push commit message must come from the pushlog title.

## Secret-handling rules (mandatory)

The pushlog is committed to the repository. A leaked secret here is permanent in git history. These rules apply **even if the secret-pattern verifier (step 6) would catch it** — the verifier is a backstop, not the primary defense.

- **Never quote literal secret values from a diff** in bullets. This includes API keys (`sk-…`, `sk-ant-…`, `ghp_…`, `xox[bp]-…`), JWTs (`eyJ…`), AWS access keys (`AKIA…`), Google API keys (`AIza…`), Bearer tokens, OAuth tokens, passwords, DB connection strings with credentials, PEM/private-key blocks, or any high-entropy random string from a diff.
- **`[REDACTED-SENSITIVE-FILE]` in `CHANGED_FILES`** means the script's path filter caught a sensitive file (`.env`, `*.pem`, `*.key`, `*.crt`, `*.p12`, `*.pfx`, `*.gpg`, `*.jks`, `*.keystore`, `id_rsa`, `secrets.*`, `credentials.*`, `service-account*.json`, `auth.json`, `.netrc`, `.npmrc`, `.pypirc`, `*.tfvars`, `*.tfstate`, `.aws/credentials`, `.kube/*`, `.docker/config.json`, `.ssh/*`, `.gnupg/*`, etc.). Do **not** run `git diff` on the original path to "see what changed" — write a generic intent-only bullet such as `- rotated credentials in a sensitive config file (path withheld)`. Never reconstruct or guess the redacted path in your bullet text.
- **For non-redacted files that nonetheless contain secret-looking diffs** (e.g. a fixture file, a config that wasn't on the denylist), describe the *intent* — `added new env var binding` or `wired up the new API client` — never the value or even the variable name if it's secret-bearing.
- **PII** (emails, phone numbers, real names) follows the same rule unless it's explicitly task-relevant and already public in the repo.
- **When in doubt, redact.** A vaguer bullet is recoverable; a leaked secret in committed history requires rotation + history rewrite.
- **The "I'm explaining the bug" trap (mandatory)**: when documenting debugging stories that compare two forms of a value — URL-encoding (raw vs `%`-encoded), escaping (single-quoted vs literal), parsing/interpolation (input vs output), Base64/hex/JSON encoding — the LLM is tempted to quote BOTH forms "so the reader can see the transformation." DO NOT. Replace both forms with placeholders (`<RAW>` / `<URL-ENCODED>`, or generic `<value>` / `<value-encoded>`) and describe the bug structurally. Example: *"URL-encoding the `@` and `!` chars in the DB password (raw → `%`-encoded form) to fix configparser interpolation breakage"* — never quote either side. The bug story is preserved; the secret isn't. The `--verify` scan only catches known token *shapes* (`sk-…`, `AKIA…`, `eyJ…`); an arbitrary password matches no pattern and slips through unless this rule is followed at write time.

## Pre-conditions

- Must be run from a git repository root (script exits 1 otherwise)
- `chatlog` must have been invoked first in the current session
- `git`, `bash`, `awk`, `sed`, `perl` must be available (all macOS defaults)

## Invocation

```bash
bash ~/.agents/skills/pushlog/scripts/pushlog.sh
```

The script reads `pwd` to find the project and emits to stdout. No arguments. No env vars required.

### Companion script (manual, read-only — not part of the push flow)

`scripts/audit-render-status.sh` — fleet-wide audit of pushlog/chatlog files across the dev roots: reports each repo's pushlog/chatlog entry counts and GitHub visibility as TSV (pipe to `column -t -s $'\t'`), for spotting repos worth checking for legacy `• ` bullets. Makes zero file mutations. Roots default to the standard dev trees; override with colon-separated `PUSHLOG_AUDIT_ROOTS`.

## Entry format (example)

```markdown
**fix session cleanup order; add test coverage** [08Apr26 / 11.47a]
- fixed `cleanup_session()` calling `close_db()` before `flush_logs()` — logs were being dropped on shutdown (`src/session_manager.py:142-158`)
- added `tests/test_session_cleanup.py` with 3 cases covering normal/error/timeout paths
- added `.pytest_cache/` to rsync excludes (`bin/push.sh:38`)

---
```

## Anti-patterns

- ❌ **Don't add `pushlog.md`/`chatlog.md`/`CHANGELOG.md` bullets** — the script filters them out of `CHANGED_FILES`. Don't add them back from memory.
- ❌ **Don't invent timestamps** — always use the `TIMESTAMP` from the script's stdout blob.
- ❌ **Don't fabricate bullets for an empty diff** — the script exits cleanly when there's nothing to log. If you see "No changes to log", stop; don't write an entry from conversation context.
- ❌ **Don't pad bullets to feel thorough** — the opposite of a hard cap is not "as long as possible"; it is "as long as the change earns."
- ❌ **Don't pack receipts into the title** — file paths, symbol names, line ranges, count fractions (`22/22`, `5→10`), milestone/phase IDs (`M18`, `Phase 4`), and mechanism stacks joined by `+`/`with`/`via`/`/` belong in bullets. The title is the shape of the push; bullets are the proof. A reader scanning `pushlog.md` headers should understand *what changed* without needing to expand a single entry.
- ❌ **Don't skip the `--verify` step** — even if you're confident no secrets leaked, run it. It's the cheap insurance that catches what every other layer missed.
- ❌ **Don't use `• ` (U+2022) as the bullet marker** — CommonMark recognizes only `-`, `*`, `+`, `1.`, so consecutive `•` lines render as one soft-wrapped paragraph on github.com. Use `- `.
