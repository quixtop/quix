# keyscan

Find secrets before they go out — key-shaped values and secret-named files, in a folder, the staged changes or git history; shows where, never the value. Needs: git for staged and history scans; gitleaks, optional.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- keyscan
```

## Requires

- [git](https://git-scm.com) — for -s, -H and a repo's own file list
- [gitleaks](https://github.com/gitleaks/gitleaks) — optional — its rules run too when installed

## Usage

```text
keyscan — find secrets before they go out: key-shaped values (private keys,
AWS, GitHub, Slack, OpenAI, Anthropic, Stripe, SendGrid, GitLab, npm, Google,
JWTs, OpenRouter, Langfuse, Telegram bots, Slack/Discord webhooks,
SECRET_KEY=…, Bearer tokens) and secret-named files (.env, *.pem, *.key,
id_rsa, credentials.json, …). Read-only. A hit is shown as where it is, its
first 4 characters and [the rules that matched it], never the value.
With gitleaks installed its ~200 rules run too, in every mode (encoded
values decoded), with values hidden; a place both find is shown once.

Usage: keyscan [path...]        the files under each path (default: .); in a
                                git repo the files git would commit (tracked,
                                and untracked but not ignored); a file or a
                                symlink named outright is always scanned
       keyscan -a|--all [path]  every file, ignored ones too
       keyscan -s|--staged      the lines staged for the next commit
       keyscan -H|--history     every line ever added, in every commit of every
                                branch, stashes and merge resolutions included
       keyscan -H --range B..H  only the commits in that range
       keyscan -                standard input, binary included
       keyscan --mask FILE      FILE with every line holding a match replaced by
                                ‹redacted:rule› (whole private-key blocks too);
                                honours no skip; prints nothing and exits 1 if
                                gitleaks is missing (unless --no-engines), cannot
                                run, or its report cannot be trusted
       keyscan --strict …       honour no allow marker and no .gitleaksignore
                                (paths and - only)
       keyscan --json …         one JSON object per hit or note, then a summary;
                                the status line goes to stderr
       keyscan --no-engines …   keyscan's own patterns only, no gitleaks
       keyscan -h|--help|help

Exit: 0 clean · 1 a hit, or something it could not read or run · 2 the scan
could not run (a missing path, not a repo, git or grep failing outright).
Skipped, and counted on the closing line: a line holding "keyscan:allow",
"secscan:allow" or "gitleaks:allow" (fake keys in test fixtures); a
documented example key (one ending in EXAMPLE, as AWS's docs use); a place
listed in .gitleaksignore at the repo's top (outside git: the current
folder), whatever rule caught it — one gitleaks fingerprint per line:
file:rule:line, or commit:file:rule:line for a history hit (file:rule:line
skips that place in every commit, as gitleaks reads it). A .gitleaks.toml
inside the scanned folder is not read (GITLEAKS_CONFIG / GITLEAKS_CONFIG_TOML,
when set, apply); gitleaks itself may still honour a .gitleaksignore at a
scanned folder's top whose entries hold absolute paths — under --strict that
file is a hit.
Git's own settings never narrow a scan: names are read from the repo's top,
whatever diff.relative, log.showRoot, diff.noprefix or .gitattributes say.
Paths mode decodes UTF-16 text (with its byte-order mark) and scans it; other
binary files are not read, and the closing line counts them; a nested
repository or submodule is not scanned, and is counted too — scan it on its own.
--json names every file exactly (control bytes as \u00XX); text output shows them as ?.
The first signature list is a verbatim copy of ~/.claude/hooks/secret-patterns.sh,
the rest push's and pushlog's extras and keyscan's own;
~/.agents/tests/skills/pushlog/test_secret_patterns.sh fails when a copy falls behind.
```

## Source

`sh/keyscan` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
