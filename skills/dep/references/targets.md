# dep — target presets (read when detecting a project's targets)
<!-- author: shrix -->

READ during § Resolving targets step 2 (Detected). Section references without a
file name are to `dep/SKILL.md`.

### Presets — examples of the shape, NOT a closed list
A target that fits none of these is still a target; describe it by its triple
and proceed. Never refuse a project for not matching a preset.
- **local service** — dev script, `Procfile`, compose file, process manager →
  *ship* the project's own restart where it has one (`pm2 restart`, compose —
  they stop and start atomically, so forcing stop-then-start on them only adds
  downtime), else stop the old process THEN start · *prove* the NEW process
  (§ Verification); "port in use" is a FAILED ship, not a warning to route
  around. Never
  background a foreground dev script and call it shipped: a start command that
  exits non-zero looks identical to a healthy one from the caller's side. No
  ship id — the report says "restarted".
- **client bundle** — extension manifest, build output dir → *ship* **build
  only** · *prove* the build (§ Verification). `dep` does NOT
  load or reload the bundle into a browser: that needs a live browser, is
  stateful, and cannot be proven headlessly. Loading is the user's own step —
  "Load unpacked" in `chrome://extensions`, or their browser's reload — and
  belongs in the developer checklist, never in `dep`'s success claim.
  (No automated path exists: branded Chrome dropped `--load-extension` at
  137, and CDP `Extensions.loadUnpacked` no longer persists to the profile —
  verified 31Jul26 on Chrome 150 and Chrome for Testing 148.)
- **hosted service** — platform config in the repo → *ship* deploy ·
  *prove* live probe on every surface it serves
- **static site** — site config + publish dir → *ship* publish · *prove*
  fetch a marker from the live URL
- **package** — registry manifest + version bump → *ship* publish · *prove*
  the new version resolves from the registry
