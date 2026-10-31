# clearCache

Reclaim disk by deleting app caches only — never data. Needs: proj-env.sh.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- clearcache
```

## Requires

- [proj-env.sh](https://github.com/quixtop/quix/blob/main/sh/proj-env.sh/README.md) — sourced at start

## Usage

```text
clearCache — reclaim disk by deleting app CACHES only. Never touches data.

Usage:
  clearCache                   Guided walkthrough — scans and shows sizes; deletes nothing.
  clearCache <App>             Clear one app's caches (preview, then [y/N]).
  clearCache all               Every closed app's caches (preview, then [y/N]).
  clearCache -c | --claude     Claude Desktop + Claude Code caches (see Claude below).
  clearCache -n | --dry-run    Report only; change nothing. Combine with any of the above.
  clearCache -f | --force      Skip the prompt.
  clearCache -h | --help       Show this help.

Examples:
  clearCache                   First time? Start here.
  clearCache Arc               Preview Arc's caches, prompt before deleting.
  clearCache all -n            See total reclaimable across every closed app.
  clearCache Spotify -f        Clear Spotify without prompting.
  clearCache --claude -n       Size Claude's caches — works while Claude runs.

What counts as CACHE (removed):
  ~/Library/Caches/<app>                     HTTP / asset cache
  .../Cache, Code Cache, GPUCache            renderer + compiled-JS caches
  .../DawnGraphiteCache, DawnWebGPUCache     shader caches
  .../Service Worker/CacheStorage|ScriptCache  site offline assets
  .../component_crx_cache, extensions_crx_cache  extension INSTALLERS
  .../CachedExtensionVSIXs                   VS Code-family extension installers
  .../OptGuideOnDeviceModel*                 re-downloadable ML models

What is NEVER touched (data):
  History · Bookmarks · Cookies · Login Data (saved passwords) · Web Data
  Local Storage · IndexedDB · Extensions · Preferences · Session Storage
  Service Worker/Database (registration index — deleting deregisters workers)
  Anything under /System, /Library, or a com.apple.* container

Claude (--claude):
  The default run treats Claude Desktop like any app: its top-level caches,
  skipped while Claude Desktop (or a process named claude) runs. --claude
  reaches further, and REFUSES instead of skipping:
  Application Support/Claude/<cache dirs above>          Desktop renderer caches
  Application Support/Claude/Partitions/*/<cache dirs>   browser pane, previews
  Caches/Claude, Caches/com.anthropic.claudefordesktop   Desktop's URL caches
  Caches/claude-cli-nodejs                               Claude Code MCP logs
  Never: sign-ins (Cookies, Local Storage, IndexedDB), vm_bundles (the VM
  and its session disk), claude-code (bundled CLI), anything in ~/.claude.
  Refuses (exit 1) while Claude Desktop, a helper, or a claude CLI or daemon
  runs — so never from inside Claude Code — and when ps cannot run to tell.
  (A claude started through a link of another name is not seen.) Deletes only
  inside Claude's own folders: a symlink leading out is skipped.

Safety:
  - SKIPS any app that is running. Detection uses `ps -Ao comm=` (the
    executable name), NOT `pgrep -f` — the latter also searches each
    process's ENVIRONMENT block, so an unrelated process carrying a long
    PATH will match an app name and produce a false "running".
  - When ps cannot run (a sandbox) or sees only part of the system, nothing can
    be seen running: one app by name is refused, and `all` skips every app. The
    walkthrough and a dry run (-n) show the sizes anyway: they delete nothing.
  - One app by name is refused while it runs; what runs is read again once the
    prompt is answered, and again before each app or folder is cleared.
  - An app is asked for by name, one at a time: a path ('/', '.', '..'), a name
    with a line break, or one of Apple's own (com.apple.*, any case) is refused,
    and a folder so named is never cleared. HOME must be this user's own folder,
    never '/'.
  - Deletes only inside an app's own folders: a cache reached through a link
    inside one is left.
  - A preview with sizes comes before anything is deleted; -f skips only the prompt.
  - Only ever removes paths whose basename is on the cache list above.
```

## Source

`sh/clearCache` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
