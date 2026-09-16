---
name: chatlog
author: shrix
description: "(shrix) Log significant chat interactions from a dev session into the project chatlog (docs/logs/chatlog.md) — project-scoped, newest-first, secret-redacting. Also invoked FIRST by the pushlog push workflow (must complete before pushlog.sh runs)."
metadata:
  version: "1.2"
  category: documentation
---

# Chat Interaction Logger

Capture significant development conversations for project context and reference.

Run at the end of a development session, after significant decisions, or as
the first step of the pushlog workflow.

---

## Project-relevance filter (mandatory)

The chatlog records **this project's** development narrative — nothing else. The project is the repo/directory that owns the chatlog file (see Auto-Detection). Before logging each interaction, run two independent tests; exclude the item if it fails **either**:

- **Path test** — did the work touch files *inside* this repo's tree? Edits to files **outside** the repo (global configs / dotfiles like `~/.zshrc` or `~/.claude/`, other repositories, system-wide tools) are off-project. Don't log them even if they happened this session.
- **Topic test** — is the discussion/decision *about this project's* code, goals, or design? Tangents (a general how-does-X-work question, an aside about another tool, debugging for a different project) are off-project even when no files changed.

**Log only** project-relevant decisions, features, debugging, and in-repo changes. When a session mixed project work with tangents, log the project parts and silently drop the rest — do **not** add a bullet noting that a tangent was skipped.

**If the entire session was off-project** (nothing passed both tests), write **no entry at all** and report that there was nothing project-relevant to log. Never manufacture an entry just to have one.

This filter is separate from the "trivial interaction" rule below: an interaction can be substantial yet off-project (exclude it), or project-relevant but minor.

---

## Auto-Detection

Find chatlog file (first found, or create first option if none exist):
- `docs/logs/chatlog.md`
- `docs/chatlog.md`
- `CHATLOG.md`

**If file doesn't exist**: Create with header using project name (from git or directory):
`# $ProjectName Chatlog`

---

## Date Format

Timestamps: `[DDMonYY/H.MMx]` where x is 'a' or 'p'
Examples: `[11Sep25/9.42p]`, `[11Sep25/9.42a]`

---

## Legacy `•` self-heal (via pushlog)

`pushlog.sh` rewrites legacy `  • ` (U+2022) bullets here to `  - `, at the 2-space-indent position only — a stray flush-left `• ` is NOT self-healed, so never write `•` in new entries. Markers only; `•` inside bullet text is untouched. **Standalone `chatlog` invocations skip this step**; migration lives in `pushlog.sh`.

---

## Secret-handling rules (mandatory)

The chatlog is committed to the repository. A leaked secret here is permanent in git history.

- **Never transcribe literal secret values** mentioned in the conversation. This includes API keys (`sk-…`, `sk-ant-…`, `ghp_…`, `xox[bp]-…`), JWTs (`eyJ…`), AWS access keys (`AKIA…`), Google API keys (`AIza…`), Bearer tokens, OAuth tokens, passwords, DB connection strings with credentials, and PEM/private-key blocks.
- **Common leak vector**: the user pastes a token into chat for debugging ("here's the failing request, the token is sk-…"). Don't echo the token in a bullet. Describe the action — `debugged auth flow with user-provided token` — not the value.
- **File contents from sensitive files** (`.env`, `secrets.*`, `credentials.*`, `*.pem`, `id_rsa`, `service-account*.json`, `auth.json`, `.netrc`, `.aws/credentials`, etc.) must never be quoted in bullets even if they were displayed in the conversation. Reference by intent: `rotated env var X` or `inspected service account scopes`, never the value or even the specific key name if it's secret-bearing.
- **PII** (emails, phone numbers, real names, home addresses) follows the same rule unless it's explicitly task-relevant and already public in the repo.
- **When in doubt, redact.** A vaguer bullet is recoverable; a leaked secret in committed history requires rotation + history rewrite. The pushlog flow runs a `--verify` scan over chatlog as well as pushlog — if you write a secret-shaped string here, that scan will fail and block the push.
- **The "I'm explaining the bug" trap (mandatory)**: when documenting debugging stories that compare two forms of a value — URL-encoding (raw vs `%`-encoded), escaping (single-quoted vs literal), parsing/interpolation (input vs output), Base64 / hex / JSON encoding — the LLM is tempted to quote BOTH forms "so the reader can see the transformation." DO NOT. Replace both forms with placeholders (`<RAW>` / `<URL-ENCODED>`, or generic `<value>` / `<value-encoded>`) and describe the bug structurally. Example bullet: *"URL-encoding the `@` and `!` chars in the DB password (raw → `%`-encoded form) to fix configparser interpolation breakage"* — never quote either side. The bug story is preserved; the secret isn't. The `--verify` scan only catches known token *shapes* (`sk-…`, `AKIA…`, `eyJ…`); an arbitrary password matches no pattern and slips through unless this rule is followed at write time. **Verifier is a backstop, not the primary defense.**

---

## Execution Steps

### Step 1: Capture Session

Log significant interactions from current development session:
- Important questions and answers
- Key decisions made
- Major features implemented
- Significant debugging sessions
- Architecture discussions

### Step 2: Generate Summary

Create bullet-point summary for the session:
- **Session title**: ONE timestamp (current time when chatlog is run), followed by a `>` bold summary line
- **Title casing**: title body is lowercase prose (verbs, common nouns, adjectives), but **keep acronyms and proper nouns capitalized** so readers can identify them at a glance — `PRD`, `OAuth`, `API`, `CLI` and the like, plus product and brand names (`OpenAI`, `macOS`, `YouTube`, `TypeScript`). File-name fragments matching actual filenames stay lowercase (e.g., `arch`, `func`, `spec` referencing `arch.md`/`func.md`/`spec.md`).
- **Bullets**: plain `- ` (markdown list marker — so entries render as a real bulleted list on github.com; do NOT use `• ` (U+2022) which markdown does not recognize as a list marker and folds consecutive lines into a soft-wrapped paragraph) — NO individual timestamps on each bullet
- Brief description of what was done and key outcomes
- File references where applicable

### Step 3: Insert Entry at TOP

Add entries to chatlog file **at the TOP** (after header):
- Insert between header and previous entries
- Reverse chronological: newest first
- Maintain existing format consistency

### Step 4: Confirm Success

Display completion message.

---

## Session Title Format

The top title for each session entry uses **the current time when chatlog is run** — never a date range.

✅ `[16Feb26/12.50a]` — single timestamp (time of logging)
❌ `[17Mar26/10.00p–18Mar26/12.40p]` — no ranges

## Entry Format Example

```markdown
[13Oct25/8.15p]
> **Playon/playoff command migration; shell script refactor**
- Created shell scripts in `bin/` with complete process cleanup
- Added slash commands in `.claude/commands/`
- Updated `AGENTS.md` and `docs/agent/guide.md`
- Result: Users can now use /playon, playon, or ./bin/playon.sh
```

**The `> **title**` line and every `- ` bullet start flush-left at column 0** — no leading indent (the bare timestamp, title, and bullets all begin at the start of the line). Markdown ignores up to 3 leading spaces, so indented legacy entries render identically; flush-left just keeps the raw log clean.

**No blank line between the `> **title**` blockquote and the first `- ` bullet** — put the bullets directly under the title. GitHub's cmark-gfm closes the blockquote and starts the `<ul>` cleanly without a separator, so the entry stays compact.

---

## Anti-Patterns


❌ **Don't log trivial interactions** - Skip "hi", "thanks", simple confirmations


❌ **Don't write full transcripts** - Bullet point summaries only

❌ **Don't duplicate pushlog content** - Chatlog captures conversation context, pushlog captures git changes

❌ **Don't log without file references** - Include relevant files when applicable




---

## Output

After completion, show:
```
✅ Chat successfully logged in chatlog :)
📝 Entries added to [chatlog file]
```
