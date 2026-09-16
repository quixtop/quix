#!/bin/bash
# pushlog.sh — deterministic pushlog entry generator
# --------------------------------------------------
# Captures git diff state as a structured stdout blob for the LLM to
# summarize into bullets. Handles first-run setup, initial-commit
# scenarios, and meta-file exclusion so the LLM only sees real changes.
#
# Usage:
#   ./pushlog.sh                # normal run — emit structured blob
#
# Exit codes:
#   0 — success (blob emitted, first-run setup done, or nothing to log)
#   1 — precondition failure (not in a git repo, corrupt state, etc.)

set -e

# ============================================================
# Configuration
# ============================================================

# Resolve real script dir (follow symlinks — ~/.claude/skills/ is symlinked)
SCRIPT_DIR="$(cd "$(dirname "$(readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")" 2>/dev/null && pwd)"
# Fallback if the above doesn't resolve (direct invocation with no symlink)
[ -z "$SCRIPT_DIR" ] && SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source project detection helpers (PROJECT_NAME, IS_GIT_REPO, colors)
source "$SCRIPT_DIR/proj-env.sh"
detect_project

# Meta-files that must never appear in pushlog bullets (R5)
META_FILES=(
    "docs/logs/pushlog.md"
    "docs/pushlog.md"
    "PUSHLOG.md"
    "CHANGELOG.md"
    "docs/logs/chatlog.md"
    "docs/chatlog.md"
    "CHATLOG.md"
)

# Threshold above which we add a "net change:" footer bullet to entries
LARGE_ENTRY_FILE_THRESHOLD=10

# ============================================================
# Precondition checks
# ============================================================

if [ "$IS_GIT_REPO" != true ]; then
    printf '%bError: not in a git repository%b\n' "$RED" "$NC" >&2
    exit 1
fi

# ============================================================
# File path auto-detection
# ============================================================

# Prefer existing files; fall back to docs/logs/ default for first-run
PUSHLOG_FILE=""
for candidate in docs/logs/pushlog.md docs/pushlog.md PUSHLOG.md; do
    if [ -f "$candidate" ]; then
        PUSHLOG_FILE="$candidate"
        break
    fi
done
PUSHLOG_FILE="${PUSHLOG_FILE:-docs/logs/pushlog.md}"

CHATLOG_FILE=""
for candidate in docs/logs/chatlog.md docs/chatlog.md CHATLOG.md; do
    if [ -f "$candidate" ]; then
        CHATLOG_FILE="$candidate"
        break
    fi
done
CHATLOG_FILE="${CHATLOG_FILE:-docs/logs/chatlog.md}"

# ============================================================
# Helper functions
# ============================================================

# Normalize project name for pushlog header (R4).
# - Prefer git remote basename over pwd
# - Strip -v2 / _v3 version suffixes
# - Replace - and _ with space
# - Titlecase first char only (macOS-compatible via perl)
display_project_name() {
    local raw
    raw=$(git config --get remote.origin.url 2>/dev/null | sed 's|.*/||; s|\.git$||')
    [ -z "$raw" ] && raw=$(basename "$(pwd)")
    # Strip version suffixes, normalize separators to spaces, titlecase first char.
    # Using sed for separator replacement (not tr) because macOS BSD tr parses '-_' as an option flag.
    raw=$(printf '%s' "$raw" | sed -E 's/[-_]v[0-9]+$//' | sed 's/[-_]/ /g')
    printf '%s' "$raw" | perl -pe 's/^./\u$&/'
}

# Pushlog timestamp: "08Apr26 / 11.47a" (spaces around /)
format_pushlog_timestamp() {
    date '+%d%b%y / %l.%M%p' | tr -s ' ' | sed 's/PM/p/; s/AM/a/'
}

# Write the pushlog header. Title underline matches title length.
write_pushlog_header() {
    local display="$1"
    local title="$display Push Logs"
    local underline
    underline=$(printf '%.0s-' $(seq 1 ${#title}))
    cat > "$PUSHLOG_FILE" <<EOF
$title
$underline

EOF
}

# Write the chatlog header (project-scoped, matching SKILL.md spec)
write_chatlog_header() {
    local display="$1"
    cat > "$CHATLOG_FILE" <<EOF
# $display Chatlog

EOF
}

# Scan a log file for known secret patterns. Emits a count-only warning
# (never the matched value) and returns non-zero on hit.
#
# Scope is format-specific:
#   - pushlog: extracts from the first `**...**` title line up to the next
#     `---` separator — i.e. only the topmost (newest) entry. Older entries
#     below the first separator are skipped.
#   - chatlog: scans the full file. Chatlog uses `  > **title**` indented
#     titles (not `^**`) and has no `---` separators, so structural extraction
#     is unreliable. Full-file scan trades a few false positives on old
#     entries for guaranteed coverage of the freshly-written one.
scan_log_for_secrets() {
    local file="$1"
    local label="$2"
    [ ! -f "$file" ] && return 0

    local entry
    if [ "$label" = "chatlog" ]; then
        entry=$(cat "$file")
    else
        entry=$(awk '
            /^\*\*/ && !found { found=1 }
            found && /^---$/ { exit }
            found { print }
        ' "$file")
    fi
    [ -z "$entry" ] && return 0

    # Known secret prefixes / formats. Conservative — chosen so prose like
    # "Bearer auth" or "AKIA" alone won't trip; we require key-shaped suffixes.
    local patterns='(sk-ant-[A-Za-z0-9_-]{20,})'
    patterns="$patterns"'|(sk-[A-Za-z0-9_-]{20,})'
    patterns="$patterns"'|(gh[pousr]_[A-Za-z0-9]{30,})'
    patterns="$patterns"'|(xox[baprs]-[A-Za-z0-9-]{20,})'
    patterns="$patterns"'|(AKIA[0-9A-Z]{16})'
    patterns="$patterns"'|(AIza[0-9A-Za-z_-]{35})'
    patterns="$patterns"'|(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+)'
    patterns="$patterns"'|(Bearer [A-Za-z0-9_.-]{20,})'
    patterns="$patterns"'|(-----BEGIN [A-Z ]*PRIVATE KEY-----)'

    # grep -c prints the match count to stdout and exits 1 on zero matches.
    # We swallow that exit (and any grep crash) by falling back to count=0.
    # Net effect: a broken grep silently passes the scan rather than erroring.
    local count
    count=$(printf '%s' "$entry" | grep -cE "$patterns" 2>/dev/null) || count=0
    if [ "$count" -gt 0 ]; then
        printf '%b⚠️  POSSIBLE SECRET LEAK in %s — %d line(s) matched a known secret pattern.%b\n' "$RED" "$label" "$count" "$NC" >&2
        printf '%b   File: %s%b\n' "$RED" "$file" "$NC" >&2
        if [ "$label" = "chatlog" ]; then
            printf '%b   Note: chatlog has no entry separators, so the scan covers the full file.%b\n' "$RED" "$NC" >&2
            printf '%b   The match may be in an older entry; check the most recently added bullets first.%b\n' "$RED" "$NC" >&2
        fi
        printf '%b   Inspect manually and redact before pushing.%b\n' "$RED" "$NC" >&2
        return 1
    fi
    return 0
}

# --verify mode: scan top entries of pushlog + chatlog and exit. Run as the
# LAST step after the LLM has written the entry, before any commit/push.
if [ "${1:-}" = "--verify" ]; then
    rc=0
    scan_log_for_secrets "$PUSHLOG_FILE" "pushlog" || rc=1
    scan_log_for_secrets "$CHATLOG_FILE" "chatlog" || rc=1
    if [ "$rc" -eq 0 ]; then
        printf '%b✓ Secret-pattern scan clean (pushlog top entry + full chatlog)%b\n' "$GREEN" "$NC"
    fi
    exit $rc
fi

# Filter meta-files out of `git diff --name-status` output (R5),
# AND redact paths of likely secret-bearing files so neither the path nor its
# contents can leak into pushlog bullets via the LLM. Sensitive entries are
# replaced with `[REDACTED-SENSITIVE-FILE]` rather than dropped, so the LLM
# still knows a sensitive file changed and can write a generic bullet.
filter_meta_files() {
    awk '
        function is_sensitive(p,    n, parts, base) {
            n = split(p, parts, "/")
            base = parts[n]
            # .env, .env.local, .env.production, foo.env etc.
            if (p ~ /(^|\/)\.env(\.|$)/ || base ~ /\.env$/) return 1
            # cryptographic material
            if (base ~ /\.(pem|key|crt|cer|p12|pfx|gpg|asc|jks|keystore)$/) return 1
            if (base ~ /^id_(rsa|ed25519|ecdsa|dsa)(\.pub)?$/) return 1
            # well-known credential filenames.
            # ⚠️ These two rungs match a NAME, not a format — unlike .pem/.key/.env/.tfvars above,
            # which identify a file that IS a credential store. So a documentation extension is
            # exempted: `secrets.md` is prose ABOUT secrets (cf-worx keeps docs/secrets.md — the
            # names of every secret and which Worker binds it, values never recorded), and
            # redacting it produced a vague, useless bullet on every push that touched it while
            # protecting nothing. A real credential store is never a .md.
            if (base ~ /^secrets?\./ && base !~ /\.(md|txt|rst|adoc)$/) return 1
            if (base ~ /^credentials?\./ && base !~ /\.(md|txt|rst|adoc)$/) return 1
            if (base ~ /^service[-_]account.*\.json$/) return 1
            if (base == "auth.json" || base == ".netrc" || base == ".npmrc" || base == ".pypirc") return 1
            # infrastructure-as-code with embedded secrets (Terraform)
            if (base ~ /\.tfvars$/) return 1
            if (base ~ /\.tfstate(\.backup)?$/) return 1
            # well-known credential directories
            if (p ~ /(^|\/)\.aws\/credentials$/) return 1
            if (p ~ /(^|\/)\.kube\//) return 1
            if (p ~ /(^|\/)\.docker\/config\.json$/) return 1
            if (p ~ /(^|\/)\.ssh\//) return 1
            if (p ~ /(^|\/)\.gnupg\//) return 1
            return 0
        }
        BEGIN {
            meta["docs/logs/pushlog.md"] = 1
            meta["docs/pushlog.md"] = 1
            meta["PUSHLOG.md"] = 1
            meta["CHANGELOG.md"] = 1
            meta["docs/logs/chatlog.md"] = 1
            meta["docs/chatlog.md"] = 1
            meta["CHATLOG.md"] = 1
        }
        NF >= 2 && (meta[$2] || meta[$NF]) { next }
        NF >= 2 {
            sensitive = is_sensitive($2)
            if (NF >= 3) sensitive = sensitive || is_sensitive($NF)
            if (sensitive) {
                print $1 "\t[REDACTED-SENSITIVE-FILE]"
            } else {
                print
            }
        }
    '
}

# One-time, idempotent migration of legacy `•` (U+2022) bullet markers to
# `- ` (markdown list marker). The skill originally used `•` because of an
# aesthetic preference; this turned out to render as a single soft-wrapped
# paragraph blob on github.com (CommonMark only recognizes `-`/`*`/`+`/`1.`
# as list markers, NOT `•`). The skill now writes `- ` for new entries; this
# function self-heals existing entries in legacy files so older content also
# renders as a real bulleted list once the user's next push lands.
#
# Idempotency: after the first conversion, no lines starting with `^• ` (or
# `^  • ` for chatlog) remain, so subsequent runs are no-ops.
# Safety: only matches BULLET-MARKER positions (line start + optional 2-space
# indent for chatlog). Cannot match `•` appearing inside bullet text or in
# code blocks (which require 4+ leading spaces).
# Portability: uses `perl -pi` rather than `sed -i` because `sed -i` requires
# different syntax on BSD/macOS vs GNU/Linux.
migrate_legacy_bullets() {
    local push_n=0 chat_n=0
    if [ -f "$PUSHLOG_FILE" ]; then
        push_n=$(grep -cE '^• ' "$PUSHLOG_FILE" 2>/dev/null) || push_n=0
        if [ "$push_n" -gt 0 ]; then
            perl -pi -e 's/^\xe2\x80\xa2 /- /' "$PUSHLOG_FILE"
        fi
    fi
    if [ -f "$CHATLOG_FILE" ]; then
        chat_n=$(grep -cE '^  • ' "$CHATLOG_FILE" 2>/dev/null) || chat_n=0
        if [ "$chat_n" -gt 0 ]; then
            perl -pi -e 's/^  \xe2\x80\xa2 /  - /' "$CHATLOG_FILE"
        fi
    fi
    if [ "$push_n" -gt 0 ] || [ "$chat_n" -gt 0 ]; then
        printf '%b📋 One-time bullet migration:%b legacy `•` U+2022 → `- ` (so older entries render as a bulleted list on GitHub).\n' "$YELLOW" "$NC" >&2
        [ "$push_n" -gt 0 ] && printf '   converted %d bullet(s) in %s\n' "$push_n" "$PUSHLOG_FILE" >&2
        [ "$chat_n" -gt 0 ] && printf '   converted %d bullet(s) in %s\n' "$chat_n" "$CHATLOG_FILE" >&2
        printf '   These changes will be staged with your next `git add` / push.\n' >&2
        printf '\n' >&2
    fi
}

# ============================================================
# Ensure log files exist with correct headers (R1 — non-blocking)
# ============================================================
# Every run verifies both files exist with headers. If either is missing,
# create it as a side effect and inform the user. Then continue to diff
# detection — no two-run dance required. On truly empty projects the
# script will create the files and then exit cleanly via the "nothing to
# log" path below.

PUSHLOG_CREATED=false
CHATLOG_CREATED=false
DISPLAY_NAME=$(display_project_name)

if [ ! -f "$PUSHLOG_FILE" ] || [ ! -s "$PUSHLOG_FILE" ]; then
    mkdir -p "$(dirname "$PUSHLOG_FILE")"
    write_pushlog_header "$DISPLAY_NAME"
    PUSHLOG_CREATED=true
fi

if [ ! -f "$CHATLOG_FILE" ] || [ ! -s "$CHATLOG_FILE" ]; then
    mkdir -p "$(dirname "$CHATLOG_FILE")"
    write_chatlog_header "$DISPLAY_NAME"
    CHATLOG_CREATED=true
fi

if [ "$PUSHLOG_CREATED" = true ] || [ "$CHATLOG_CREATED" = true ]; then
    printf '%b📋 Log file setup:%b\n' "$GREEN" "$NC"
    [ "$PUSHLOG_CREATED" = true ] && printf '  📝 Created %s\n' "$PUSHLOG_FILE"
    [ "$CHATLOG_CREATED" = true ] && printf '  💬 Created %s\n' "$CHATLOG_FILE"
    printf '\n'
fi

# Self-heal legacy `•` bullets on existing files (idempotent — runs every
# time but does nothing once a file has been migrated).
migrate_legacy_bullets

# ============================================================
# Diff range detection
# ============================================================

TOTAL_COMMITS=$(git rev-list --count HEAD 2>/dev/null || echo "0")
EMPTY_TREE=$(git hash-object -t tree /dev/null)
IS_INITIAL_COMMIT=false

# Helper: detect any working-tree work, including untracked files.
# `git diff --quiet HEAD` only sees tracked modifications; `git status --porcelain`
# catches both tracked mods and untracked files (which are often exactly what the
# user is about to `git add` and push).
working_tree_has_changes() {
    [ -n "$(git status --porcelain 2>/dev/null)" ]
}

if [ "$TOTAL_COMMITS" = "0" ]; then
    # Pre-initial-commit state: working tree vs empty tree
    DIFF_RANGE="$EMPTY_TREE"
    IS_INITIAL_COMMIT=true
elif [ "$TOTAL_COMMITS" = "1" ] && ! git rev-parse '@{u}' >/dev/null 2>&1 && ! working_tree_has_changes; then
    # Only initial commit, no upstream, clean tree — log the initial commit itself.
    # (If the tree is dirty, fall through to normal mode so working-tree changes get logged instead.)
    DIFF_RANGE="$EMPTY_TREE..HEAD"
    IS_INITIAL_COMMIT=true
else
    # Normal case: prefer commits-ahead-of-upstream, fall back to working tree
    if git rev-parse '@{u}' >/dev/null 2>&1; then
        AHEAD=$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo "0")
        if [ "$AHEAD" -gt 0 ]; then
            DIFF_RANGE='@{u}..HEAD'
        elif working_tree_has_changes; then
            DIFF_RANGE="HEAD"
        else
            printf '%bNo changes to log%b — working tree clean, no commits ahead of upstream.\n' "$YELLOW" "$NC"
            exit 0
        fi
    else
        if working_tree_has_changes; then
            DIFF_RANGE="HEAD"
        else
            printf '%bNo changes to log%b — working tree clean, no upstream configured.\n' "$YELLOW" "$NC"
            exit 0
        fi
    fi
fi

# ============================================================
# Collect diff data
# ============================================================

CHANGED_FILES_RAW=$(git diff --name-status "$DIFF_RANGE" 2>/dev/null || true)
DIFF_STAT=$(git diff --shortstat "$DIFF_RANGE" 2>/dev/null || true)

# In working-tree mode (DIFF_RANGE=HEAD or pre-initial-commit), also include
# untracked files — they're exactly what the user is about to commit/push.
# Not applicable when DIFF_RANGE is a commit range (@{u}..HEAD etc) because
# untracked files are irrelevant to already-committed history.
if [ "$DIFF_RANGE" = "HEAD" ] || [ "$DIFF_RANGE" = "$EMPTY_TREE" ]; then
    UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | awk 'NF { print "A\t" $0 }')
    if [ -n "$UNTRACKED" ]; then
        if [ -n "$CHANGED_FILES_RAW" ]; then
            CHANGED_FILES_RAW=$(printf '%s\n%s' "$CHANGED_FILES_RAW" "$UNTRACKED")
        else
            CHANGED_FILES_RAW="$UNTRACKED"
        fi
    fi
fi

# Filter meta-files (R5)
CHANGED_FILES=$(printf '%s\n' "$CHANGED_FILES_RAW" | filter_meta_files)

# Count filtered files
if [ -z "$CHANGED_FILES" ]; then
    FILE_COUNT=0
else
    FILE_COUNT=$(printf '%s\n' "$CHANGED_FILES" | grep -c '^')
fi

# Abort if nothing real to log (either all meta-files or truly empty)
if [ "$FILE_COUNT" = "0" ]; then
    if [ "$IS_INITIAL_COMMIT" = true ]; then
        printf '%bNo changes to log%b — initial state is empty or only contains meta-files.\n' "$YELLOW" "$NC"
    else
        printf '%bNo changes to log%b — only meta-file (pushlog/chatlog) updates found.\n' "$YELLOW" "$NC"
    fi
    exit 0
fi

IS_LARGE_ENTRY=false
if [ "$FILE_COUNT" -ge "$LARGE_ENTRY_FILE_THRESHOLD" ]; then
    IS_LARGE_ENTRY=true
fi

TIMESTAMP=$(format_pushlog_timestamp)

# Parse shortstat counts (reused for both initial-commit + net-change footer)
FILES_N=$(printf '%s' "$DIFF_STAT" | grep -oE '[0-9]+ files?' | head -1 | awk '{print $1}')
INS_N=$(printf '%s' "$DIFF_STAT" | grep -oE '[0-9]+ insertions?' | head -1 | awk '{print $1}')
DEL_N=$(printf '%s' "$DIFF_STAT" | grep -oE '[0-9]+ deletions?' | head -1 | awk '{print $1}')
FILES_N="${FILES_N:-0}"
INS_N="${INS_N:-0}"
DEL_N="${DEL_N:-0}"
TOTAL_LINES=$((INS_N + DEL_N))

# ============================================================
# Initial-commit case (R2): emit preformatted entry
# ============================================================

if [ "$IS_INITIAL_COMMIT" = true ]; then
    cat <<EOF
=== PUSHLOG SCRIPT OUTPUT ===
MODE=initial_commit
PUSHLOG_FILE=$PUSHLOG_FILE
CHATLOG_FILE=$CHATLOG_FILE
TIMESTAMP=$TIMESTAMP
DIFF_RANGE=$DIFF_RANGE
FILE_COUNT=$FILE_COUNT

=== PREFORMATTED ENTRY (write this verbatim to the top of \$PUSHLOG_FILE, after the header block) ===
**initial project scaffold** [$TIMESTAMP]
- initial project scaffold ($FILE_COUNT files, ~$TOTAL_LINES lines)

---

=== INSTRUCTIONS FOR LLM ===
(Assumed flow per SKILL.md: chatlog has already run before this script.)
1. Prepend the preformatted entry above to $PUSHLOG_FILE directly after the header block
2. Do NOT generate additional bullets — the single-bullet scaffold summary is intentional
=== END ===
EOF
    exit 0
fi

# ============================================================
# Normal case: emit structured data for LLM summarization
# ============================================================

NET_CHANGE_FOOTER=""
if [ "$IS_LARGE_ENTRY" = true ]; then
    # Use FILE_COUNT (filtered + includes untracked) rather than FILES_N (shortstat-only),
    # so the file count matches the CHANGED_FILES list the LLM is summarizing.
    # Line counts still come from shortstat — they're authoritative for commit-range diffs
    # and approximate (tracked-mods-only) for working-tree diffs.
    NET_CHANGE_FOOTER="- net change: ${FILE_COUNT} files, +${INS_N} −${DEL_N} lines"
fi

cat <<EOF
=== PUSHLOG SCRIPT OUTPUT ===
MODE=normal
PUSHLOG_FILE=$PUSHLOG_FILE
CHATLOG_FILE=$CHATLOG_FILE
TIMESTAMP=$TIMESTAMP
DIFF_RANGE=$DIFF_RANGE
FILE_COUNT=$FILE_COUNT
IS_LARGE_ENTRY=$IS_LARGE_ENTRY

=== CHANGED_FILES (meta-files already filtered out) ===
$CHANGED_FILES

=== DIFF_STAT ===
$DIFF_STAT
EOF

if [ -n "$NET_CHANGE_FOOTER" ]; then
    cat <<EOF

=== NET_CHANGE_FOOTER (append as last bullet for large entries) ===
$NET_CHANGE_FOOTER
EOF
fi

cat <<EOF

=== INSTRUCTIONS FOR LLM ===
(Assumed flow per SKILL.md: chatlog has already run before this script — any
chatlog.md changes have been filtered out of CHANGED_FILES by the meta-file filter.)

1. Review CHANGED_FILES. Optionally run \`git diff $DIFF_RANGE -- <file>\` for per-file context.
2. Summarize into bullets using the \`- \` character (markdown list marker — renders as a real bulleted list on github.com; do NOT use \`• \` U+2022 which markdown ignores as a list marker). No artificial bullet count or char limits.
3. Write the title as \`**lowercase phrase; phrase; phrase**\` (2–4 phrases, importance order: fix > feat > refactor > docs).
4. Prepend this entry to $PUSHLOG_FILE directly after the header block (the title + underline lines):

   **<your title>** [$TIMESTAMP]
   - bullet 1 (file refs in backticks, e.g. \`src/foo.py:42-55\`)
   - bullet 2
   ... more bullets as needed
$([ -n "$NET_CHANGE_FOOTER" ] && printf '   %s\n' "$NET_CHANGE_FOOTER")

   ---
=== END ===
EOF
