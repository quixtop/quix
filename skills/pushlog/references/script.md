# pushlog.sh — what the script handles, and its companion
<!-- author: shrix -->

Read only when the script's behaviour is in question.

## What the script handles automatically

- **First-run setup** — if pushlog.md has no entries, creates both `docs/logs/pushlog.md` and `docs/logs/chatlog.md` with correct headers, then exits. Run again after changes.
- **Diff range detection** — commits ahead of upstream AND a dirty tree → `@{u}` (upstream vs the working tree, untracked files added, because `push` commits the tree too); commits ahead only → `@{u}..HEAD`; a dirty tree only → `HEAD` (working tree, untracked added); aborts cleanly with "nothing to log" if all are empty.
- **`--verify`** — scans the newest pushlog entry and the whole chatlog for key-shaped secrets (Anthropic/OpenAI, GitHub incl. `github_pat_`, GitLab, npm, Stripe live, Slack, AWS, Google, JWT, Bearer, PEM). It fails CLOSED: a scan that cannot run (grep error) is never reported clean.
- **Initial-commit scenario** — on the repo's first commit, emits a preformatted collapsed entry (`- initial project scaffold (N files, M lines)`) instead of a 30-bullet dump.
- **Meta-file exclusion** — removes `pushlog.md`, `chatlog.md`, `CHANGELOG.md`, and variants from the changed-files list so they can never appear in bullets.
- **Timestamp formatting** — deterministic `DDMonYY / H.MMp` format (e.g. `08Apr26 / 11.47a`) via `date` + `tr -s ' '` + `sed`.
- **Large-entry footer** — appends `- net change: N files, +A −B lines` for diffs touching 10+ files. Derived from `git diff --shortstat`.
- **Project name normalization** — for first-run headers, prefers `git remote origin` basename, strips version suffixes (`-v2`), replaces `-`/`_` with space, titlecases first char.
- **Legacy `•` self-heal** — rewrites legacy `• ` (U+2022) bullet markers to `- ` in both files. Markers only; `•` inside bullet text is untouched. Idempotent. Migrated lines stage with your next `git add`; stderr emits `📋 One-time bullet migration: …` with a count.

### Companion script (manual, read-only — not part of the push flow)

`scripts/audit-render-status.sh` — fleet-wide audit of pushlog/chatlog files across the dev roots: reports each repo's pushlog/chatlog entry counts and GitHub visibility as TSV (pipe to `column -t -s $'\t'`), for spotting repos worth checking for legacy `• ` bullets. Makes zero file mutations. Roots default to the standard dev trees; override with colon-separated `PUSHLOG_AUDIT_ROOTS`.

