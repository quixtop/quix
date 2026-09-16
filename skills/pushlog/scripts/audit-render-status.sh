#!/bin/bash
# audit-render-status.sh — read-only audit of pushlog/chatlog files across the
# user's dev directories. Identifies candidates for retroactively migrating
# the • → - bullet character, so existing entries render as a real bulleted
# list on github.com instead of a wrapped paragraph blob.
#
# OUTPUT: tab-separated rows (sortable/awk-friendly) listing each repo with
# pushlog/chatlog content, sorted by visibility (public first) × pushlog
# entry count (descending). Header line is prefixed with `#` so output can
# be piped to `awk -F'\t' '$1!~/^#/'` to skip it.
#
# THIS SCRIPT MAKES ZERO FILE MUTATIONS. It only reads, counts, and queries
# `git remote -v` / `gh repo view`. No `git add`, no commits, no edits.
#
# Usage:
#   bash ~/.agents/skills/pushlog/scripts/audit-render-status.sh
#   bash ~/.agents/skills/pushlog/scripts/audit-render-status.sh | column -t -s $'\t'

set -e

# Roots to scan. Override with colon-separated PUSHLOG_AUDIT_ROOTS.
if [ -n "${PUSHLOG_AUDIT_ROOTS:-}" ]; then
    IFS=':' read -r -a ROOTS <<< "$PUSHLOG_AUDIT_ROOTS"
else
    ROOTS=(
        "/Volumes/NVMe2TB/shrix/Dev"
        "/Users/shrix/Dev"
    )
fi

# Filenames the pushlog / chatlog skills auto-detect.
LOG_NAMES=(pushlog.md chatlog.md PUSHLOG.md CHATLOG.md)

# ANSI colors (only for stderr status messages — stdout stays plain TSV)
if [ -t 2 ]; then
    YELLOW=$'\033[33m'; GREEN=$'\033[32m'; DIM=$'\033[2m'; NC=$'\033[0m'
else
    YELLOW=; GREEN=; DIM=; NC=
fi

# Detect whether `gh` CLI is authenticated. Without it, repo visibility
# (public/private) cannot be determined — only the presence of a github.com
# remote, which is necessary but not sufficient.
GH_AVAILABLE=false
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    GH_AVAILABLE=true
else
    printf '%bnote:%b gh CLI not found or not authenticated — visibility column will be "unknown" for all rows.\n' "$YELLOW" "$NC" >&2
    printf '       to enable visibility detection, run: gh auth login\n' >&2
fi

# Walk each root, find candidate log files. -maxdepth 6 catches typical
# project layouts (project/docs/logs/pushlog.md = 4 levels) without descending
# into deeply nested node_modules / .venv trees that could be slow.
collect_log_files() {
    for root in "${ROOTS[@]}"; do
        [ -d "$root" ] || continue
        local find_args=("$root" -maxdepth 6 -type f)
        # Build OR-clause for filenames
        find_args+=(\()
        local first=true
        for name in "${LOG_NAMES[@]}"; do
            if [ "$first" = true ]; then
                find_args+=(-name "$name")
                first=false
            else
                find_args+=(-o -name "$name")
            fi
        done
        find_args+=(\))
        find "${find_args[@]}" 2>/dev/null
    done
}

# Walk up from a file path to find the containing .git repo root, or empty
# if no .git ancestor exists.
find_repo_root() {
    local dir
    dir=$(dirname "$1")
    while [ "$dir" != "/" ] && [ "$dir" != "." ]; do
        if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
            printf '%s\n' "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    return 1
}

# Count entries in a pushlog-style file (titles match `^**...**`, separators
# match `^---$`). For chatlog-style files, use the timestamp pattern.
count_entries() {
    local file="$1"
    local kind="$2"  # "pushlog" or "chatlog"
    [ -f "$file" ] || { printf '0\n'; return; }
    local n
    if [ "$kind" = "chatlog" ]; then
        # chatlog timestamps are `[DDMonYY/H.MMx]` at column 0
        n=$(grep -cE '^\[[0-9]{1,2}[A-Z][a-z]{2}[0-9]{2}/' "$file" 2>/dev/null) || n=0
    else
        # pushlog titles are `**...**` at column 0 (excluding the file's first-line title)
        n=$(grep -cE '^\*\*[^*].*\*\*' "$file" 2>/dev/null) || n=0
    fi
    printf '%s\n' "$n"
}

# Get GitHub visibility for a repo root. Returns one of:
#   public | private | not-github | no-remote | unknown
get_visibility() {
    local repo="$1"
    local remote
    remote=$(git -C "$repo" remote get-url origin 2>/dev/null) || { printf 'no-remote\n'; return; }
    case "$remote" in
        *github.com*) ;;
        *) printf 'not-github\n'; return ;;
    esac
    if [ "$GH_AVAILABLE" != true ]; then
        printf 'unknown\n'
        return
    fi
    # gh repo view emits JSON; extract visibility field
    local vis
    vis=$(gh repo view "$repo" --json visibility --jq '.visibility' 2>/dev/null) || { printf 'unknown\n'; return; }
    # gh returns PUBLIC / PRIVATE / INTERNAL — normalize to lowercase
    printf '%s\n' "$vis" | tr '[:upper:]' '[:lower:]'
}

# Pretty project name from repo root (basename, but strip -v2/_v3 suffixes
# like the main pushlog script does — so output matches the user's mental
# model of project naming).
display_name() {
    local repo="$1"
    local raw
    raw=$(basename "$repo")
    # Strip trailing version suffixes
    printf '%s' "$raw" | sed -E 's/[-_]v[0-9]+$//'
}

# ============================================================
# Main
# ============================================================

printf '%bscanning roots:%b %s\n' "$DIM" "$NC" "${ROOTS[*]}" >&2

# Collect all log files, group by repo root, dedupe.
declare -A REPO_LOGS  # repo_root -> "pushlog_path|chatlog_path"
total_files=0
while IFS= read -r logfile; do
    [ -n "$logfile" ] || continue
    total_files=$((total_files + 1))
    repo_root=$(find_repo_root "$logfile") || continue
    [ -n "$repo_root" ] || continue
    # Initialize entry if first time seeing this repo
    if [ -z "${REPO_LOGS[$repo_root]+x}" ]; then
        REPO_LOGS[$repo_root]="|"
    fi
    # Decide push vs chat slot based on filename
    base=$(basename "$logfile")
    case "$base" in
        pushlog.md|PUSHLOG.md)
            current="${REPO_LOGS[$repo_root]}"
            REPO_LOGS[$repo_root]="${logfile}|${current#*|}"
            ;;
        chatlog.md|CHATLOG.md)
            current="${REPO_LOGS[$repo_root]}"
            REPO_LOGS[$repo_root]="${current%|*}|${logfile}"
            ;;
    esac
done < <(collect_log_files)

printf '%bfound:%b %d log files across %d repos\n' "$GREEN" "$NC" "$total_files" "${#REPO_LOGS[@]}" >&2
printf '\n' >&2

# Emit TSV header (prefixed with # so it's easy to filter out)
printf '# %s\t%s\t%s\t%s\t%s\t%s\n' "project" "visibility" "push_n" "chat_n" "repo_path" "log_paths"

# Per-repo: count entries, query visibility, emit row
for repo_root in "${!REPO_LOGS[@]}"; do
    paths="${REPO_LOGS[$repo_root]}"
    pushlog="${paths%|*}"
    chatlog="${paths#*|}"

    push_n=$(count_entries "$pushlog" pushlog)
    chat_n=$(count_entries "$chatlog" chatlog)
    visibility=$(get_visibility "$repo_root")
    project=$(display_name "$repo_root")

    # Compact log_paths column: just basenames + relative dir if both present
    log_summary=""
    [ -n "$pushlog" ] && log_summary="${pushlog#$repo_root/}"
    [ -n "$chatlog" ] && log_summary="${log_summary:+$log_summary, }${chatlog#$repo_root/}"

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$project" "$visibility" "$push_n" "$chat_n" "$repo_root" "$log_summary"
done | sort -t$'\t' -k2,2 -k3,3nr   # primary: visibility (public sorts before private alphabetically), secondary: push_n desc

printf '\n' >&2
printf '%bsort key:%b visibility (public first), then pushlog entry count (descending)\n' "$DIM" "$NC" >&2
printf '%btip:%b pipe to `column -t -s $'"'"'\\t'"'"'` for aligned output\n' "$DIM" "$NC" >&2
