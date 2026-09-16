# dep — platform mechanics
<!-- author: shrix -->

Read this ONLY when a PUBLISHED target is in play — during target DETECTION
(the `detect` rows below are where the published-target signals live) or when
one is actually
being shipped, and then only the relevant entries. `SKILL.md` owns the
pipeline, the gate, what counts as evidence, and the local-service mechanics —
those are short enough to live in the preset, and a local dep is the FAST
path, so it must not pay a file read.
This file owns the per-platform *commands and behaviors* those steps need.

Each entry answers four things: how to **detect** it, how to **ship** it, what
its **ship id** is, and what its **propagation** behavior means for step 4.

## Cloudflare (Workers / Pages)

| | |
|---|---|
| detect | `wrangler.toml` / `wrangler.jsonc` |
| ship | `cd <dir> && wrangler deploy` — the LOCALLY-INSTALLED binary, not `npx` |
| id | the `Version ID` line in the deploy output |
| propagate | seconds to a few minutes, NOT atomic across the edge |

- **Ships from its own directory.** `wrangler` reads the per-directory config
  and asset tree; running it at a repo root fails in a monorepo.
- **Non-interactive shells** need `WRANGLER_SEND_METRICS=false … </dev/null`.
  The telemetry reporter is a child process that uploads asynchronously, can
  outlive the deploy, and — in a live pipe — inherits stdout, so the reader
  never sees EOF and the run wedges. `</dev/null` also stops it blocking on a
  prompt.
- **Capture output into a variable**, don't pipe it live to `grep`/`head`: a
  wrangler child holding stdout open can hang the pipe, while a var-capture
  returns as soon as the main process exits.
- ⚠️ **Why the ship row says the local binary: concurrent `npx wrangler` calls
  race the shared npm cache lock** and the losers abort with `ECOMPROMISED` —
  the local binary does no npm resolution per call, which REMOVES the race and
  is what makes the batched parallel ship (SKILL.md § Concurrency) safe here.
  If only `npx` is available, ship serially instead. (Observed behavior, not
  documented by the vendor.)
- **The edge serves mixed versions mid-propagation**, so one probe is not
  evidence. Poll until the new marker appears on every surface, and take
  several consecutive agreeing samples before calling it converged.

## Vercel

| | |
|---|---|
| detect | `vercel.json`, or a linked `.vercel/` |
| ship | `npx vercel deploy --prod` (omit `--prod` for a preview) |
| id | the deployment URL / deployment ID in the output |
| propagate | the alias flips atomically once the build finishes |

- The build runs **remotely**, so the command returns before the code is live;
  wait for the ready state rather than assuming the exit code means serving.
- Preview vs production is the highest-stakes fact — say which one shipped.

## Fly.io

| | |
|---|---|
| detect | `fly.toml` |
| ship | `fly deploy` |
| id | the release version (`vN`) in the output |
| propagate | rolling by default — old and new machines both serve briefly |

- Multi-region apps are multiple **surfaces**: probe each region, not just the
  nearest edge.
- `fly status` after the deploy shows per-machine versions — that is the real
  convergence check.

## Container / registry targets

| | |
|---|---|
| detect | `Dockerfile`, `compose.yml`, a k8s manifest dir |
| ship | build → push → whatever applies the new tag |
| id | the image digest (NOT the tag — tags move, digests don't) |
| propagate | as slow as the orchestrator's rollout |

- Record the **digest**. A tag is a pointer and proves nothing about what ran.

## Package registries

| | |
|---|---|
| detect | `package.json`, `pyproject.toml`, `Cargo.toml` + a version bump |
| ship | the registry's publish command |
| id | the published version string |
| propagate | index/CDN lag — a fresh version may not resolve immediately |

- ⚠️ **Publishing is usually irreversible** (yank ≠ delete, and version numbers
  never come back). This is the one ship action worth confirming before running
  even inside an approved `dep`.
- `prove` = resolve the new version from the registry in a clean environment,
  not from a local cache.

## A platform not listed here

Do not guess a command. In order:
1. The project's CLAUDE.md — it usually names the deploy command already.
2. The repo's own scripts (`bin/`, `scripts/`, `Makefile`, `package.json`
   scripts) — a project that deploys has almost always scripted it.
3. Ask once, then record the answer in CLAUDE.md so no later `dep` asks again.

Then fill in the same four fields — detect / ship / id / propagate — and treat
the unknown propagation behavior as the pessimistic case: poll until every
surface agrees before reporting success.
