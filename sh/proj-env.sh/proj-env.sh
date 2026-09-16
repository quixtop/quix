#!/bin/bash
# (c) Shrix
# author: shrix
# proj-env.sh - Common environment helper script used by a few skills

# Auto-detect project configuration
detect_project() {
  PROJECT_NAME=$(basename "$(pwd)")
  PROJECT_DIR=$(pwd)
  BACKUP_DIR="${BACKUP_DIR:-../BACKUP/${PROJECT_NAME}}"
  SERVER_LOG="${SERVER_LOG:-${PROJECT_DIR}/tmp/server.log}"

  # Check if we're in a git repository
  if git rev-parse --git-dir >/dev/null 2>&1; then
    REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
    IS_GIT_REPO=true
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
  else
    REPO_URL=""
    IS_GIT_REPO=false
    CURRENT_BRANCH=""
  fi

  # Export variables for use in calling scripts
  export PROJECT_NAME PROJECT_DIR BACKUP_DIR SERVER_LOG REPO_URL IS_GIT_REPO CURRENT_BRANCH
}

# Colors for consistent output across scripts.
# Only emit ANSI escapes when stdout is a TTY — prevents log pollution
# when output is piped or redirected to a file.
if [ -t 1 ]; then
  export GREEN='\033[0;32m'
  export BLUE='\033[0;34m'
  export RED='\033[0;31m'
  export YELLOW='\033[1;33m'
  export CYAN='\033[0;36m'
  export NC='\033[0m'
else
  export GREEN='' BLUE='' RED='' YELLOW='' CYAN='' NC=''
fi

# status — the closing line every action script ends with. The blank line
# after it comes from each script's own `_gap` EXIT trap, not from here.
# Colour comes from the block above, so it is already TTY-guarded: piped or
# redirected output gets the glyph and text with no ANSI escapes.
#
#   status ok   "engine up — strm-stop · strm-status"
#   status warn "nothing to do — no .env in this project"
#   status fail "could not reach the daemon"          # then exit non-zero
#
# The glyph must agree with the exit code: never `ok` on a failing run.
status() {
  local kind="${1:-ok}" msg="${2:-}"
  case "$kind" in
    ok|OK|success)   printf "${GREEN}✓ %s${NC}\n" "$msg" ;;
    warn|WARN|partial) printf "${YELLOW}⚠ %s${NC}\n" "$msg" ;;
    fail|FAIL|error) printf "${RED}✗ %s${NC}\n" "$msg" >&2 ;;
    *)               printf "${GREEN}✓ %s${NC}\n" "$msg" ;;
  esac
}

# Display project info
show_project_info() {
  detect_project
  echo -e "${BLUE}📁 Project: ${PROJECT_NAME}${NC}"
  echo -e "${BLUE}📂 Directory: ${PROJECT_DIR}${NC}"
  if [ "$IS_GIT_REPO" = true ]; then
    echo -e "${BLUE}📡 Repository: ${REPO_URL}${NC}"
    echo -e "${BLUE}🌿 Branch: ${CURRENT_BRANCH}${NC}"
  fi
  echo -e "${BLUE}💾 Backup dir: ${BACKUP_DIR}${NC}"
  echo ""
}
