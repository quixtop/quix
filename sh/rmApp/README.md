# rmApp

Remove a Mac app and every on-disk trace it left behind. Needs: Homebrew.

## Install

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/quixtop/quix/main/sh/rmApp/rmApp -o ~/.local/bin/rmApp && chmod +x ~/.local/bin/rmApp
```

## Requires

- [Homebrew](https://brew.sh) — optional — to find brew-installed shims

## Usage

```text
rmApp — remove a Mac app and ALL its on-disk traces (~/Library, workspace dirs, PATH shims).

Usage:
  rmApp <AppName>              Preview what would be deleted, then prompt [y/N].
  rmApp -f <AppName>           Force — skip the prompt, delete immediately.
  rmApp --keep-bundle <AppName>  Clean residue only, leave /Applications/<AppName>.app alone.
  rmApp --sweep-shims          Remove dangling CLI shims (from any removed app) across PATH dirs.
  rmApp -h | --help            Show this help.

Examples:
  rmApp Slack                  Preview Slack's footprint, prompt before deleting.
  rmApp -f "Spark Desktop"     Wipe Spark Desktop without prompting.
  rmApp --keep-bundle Notion   Clear Notion's caches/data but keep the app.

  rmApp Arturia               A vendor FOLDER — removes every .app inside it,
                              each app's residue, and the folder itself.

What it does (in order):
  1. Find the bundle across /Applications, ~/Applications, /Applications/Setapp
     and /Applications/Utilities, in three shapes:
       a. <root>/<name>.app                 — the usual case
       b. <root>/<vendor>/<name>.app        — nested, e.g. Arturia/Analog Lab V
       c. <root>/<name>/ holding .app files — the vendor folder itself
     Extract every bundle ID found via `defaults read`.
  2. Quit the app gracefully via osascript.
  3. Build a candidate list across 13 standard residue locations, matching by
     both bundle ID AND app name (handles Electron apps, vendor folders, etc.).
  4. Show preview with sizes; prompt unless -f.
  5. rm -rf each path; report total reclaimed.

Safety:
  - Refuses bundle IDs starting with com.apple.* and a list of system apps
    (Finder, Safari, Mail, Messages, Terminal, etc.).
  - Refuses names shorter than 3 characters.
  - Never touches /System or /Library/ system paths (only /Library/LaunchAgents,
    /Library/LaunchDaemons, /Library/PrivilegedHelperTools, all keyed on bundle ID).
  - Dry-run by default — must explicitly confirm or pass -f.
```

## Source

`sh/rmApp` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
