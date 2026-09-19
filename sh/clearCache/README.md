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
  clearCache                   Guided walkthrough — scans, shows sizes, asks.
  clearCache <App>             Clear one app's caches (preview, then [y/N]).
  clearCache all               Every closed app's caches (preview, then [y/N]).
  clearCache -n | --dry-run    Report only; change nothing. Combine with any of the above.
  clearCache -f | --force      Skip the prompt.
  clearCache -h | --help       Show this help.

Examples:
  clearCache                   First time? Start here.
  clearCache Arc               Preview Arc's caches, prompt before deleting.
  clearCache all -n            See total reclaimable across every closed app.
  clearCache Spotify -f        Clear Spotify without prompting.

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

Safety:
  - SKIPS any app that is running. Detection uses `ps -Ao comm=` (the
    executable name), NOT `pgrep -f` — the latter also searches each
    process's ENVIRONMENT block, so an unrelated process carrying a long
    PATH will match an app name and produce a false "running".
  - Dry-run preview with sizes before anything is deleted, unless -f.
  - Only ever removes paths whose basename is on the cache list above.
```

## Source

`sh/clearCache` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
