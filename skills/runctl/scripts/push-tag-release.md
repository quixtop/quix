# /push — tagging and release modes
<!-- author: shrix -->

Read before running `push` with `-t` / `--tag` or `release`.

### Tagging (`-t | --tag [name]`, composable with the modes above)
- `push "msg" -t` → auto tag `t-YYYYMMDD-HHMMSS-<slug>` (annotated, local-only)
- `push "msg" -t <name>` → verbatim tag, pushed to origin; semver-shaped tags are immutable (FORCE=1), free labels (production, stable) roll forward with a moved-notice
- `push -t` (no msg) → backup only; time label on the folder, NO git tag
- The tag also rides the backup folder name: `last_git-<tag>`, rotating to `verN_git-<tag>`
- Sibling command: `tag` / `/tag` — tag HEAD after the fact (same shared semantics via `scripts/tag-core.sh`); use it when the push already happened
- Full matrix: `~/.agents/skills/runctl/scripts/push-README.md`

### Release (`release [branch] [flags]`)
- Promotes working branch to release branch with a semver tag
- Resolution order for release branch: explicit arg → project `.env` (`REL_BRANCH=`) → shell env `REL_BRANCH` → persisted `.git/push-rel-branch` → hardcoded `main`
- Bump flags: `-M` major, `-m` minor (default), `-p` patch; or `-t <ver>` explicit (e.g. `-t 1.7.66`)
- Tag annotation auto-built from `git log <prev-tag>..<working>`; `-n "body"` overrides
- Optional positional title → creates empty marker commit on working + uses title as annotation first line
- `-d` dry-run preview; `-y` skip confirm; `FORCE=1` for nuclear overrides
- Short flags bundle: `-Myd` = `-M -y -d` (arg-taking flags `-t`/`-n` must be last in bundle)
- Auto-creates release branch on remote if missing (confirms first unless `-y`/`FORCE=1`)
- Refuses if: on release branch already, dirty working tree, non-fast-forward, tag goes backwards, already in sync — each `FORCE=1` overridable

