# secscan — spike results (spec § 4.12.1)
Status: approved 2026-10-23

Run 2026-10-23 on the seeded fixture (`make_fixture.py`), engines gitleaks
8.30.1, trivy 0.76.1, semgrep 1.182.0, zizmor 1.31.1, actionlint, hadolint,
gosec (Homebrew), skillspector (uv tool).

| # | verdict | evidence | design consequence |
|---|---|---|---|
| S1 | ⚠️ partial | inside Claude's Bash sandbox: keyscan, gitleaks, trivy vuln + licence, zizmor, actionlint, hadolint, gosec run; **semgrep** and **skillspector** fail (the sandbox denies reading `*.pem`, which covers the public CA bundle both load at start); **trivy misconfig** fails (its checks bundle holds files named `*credentials*`, which the sandbox denies reading) | `scan.py` runs in a Terminal-panel tab when one is available (every engine works there); run through Bash, the three are `blocked` with the exact terminal command. The sandbox rule is not worked around. |
| S2 | ✅ | outside: `semgrep scan --metrics off --disable-nosem --config <cache>/semgrep/python.yml` with `HOME` in a temp folder → 2 results on the seeded SQLi, 0 errors | packs fetched by `update` with `curl https://semgrep.dev/c/p/<pack>` (default 1073 rules, python, javascript, typescript, golang, java — 3.8 MB) |
| S3 | ✅ | outside: `trivy fs --scanners vuln,misconfig,license --cache-dir <cache>/trivy --skip-db-update --skip-java-db-update --skip-check-update --offline-scan --disable-telemetry --skip-version-check --ignorefile ""` → 6 vulnerabilities in `requirements.txt`, `DS-0002` on the Dockerfile | `update`: `--download-db-only`, `--download-java-db-only`, one misconfig run to fetch the checks bundle; DB 1.5 GB + Java DB 1.5 GB |
| S4 | ✅ | gitleaks git mode with and without `--config` (`[extend] useDefault = true`) → the same rules hit | keyscan keeps the explicit config in git mode |
| S5 | ✅ | flags exist: hadolint `--disable-ignore-pragma`, gosec `-nosec`, actionlint `-config-file`, trivy `--ignorefile ""` and `--show-suppressed`, zizmor `--no-config --no-ignores`, semgrep `--disable-nosem` | as spec § 4.6; `.semgrepignore` and `trivy:ignore` stay listed as suppressions |
| S6 | ⚠️ partial | inside: blocked (CA bundle, as S1); outside: `skillspector scan --no-llm` finds the seeded injection (`SC2 External Script Fetching`, SKILL.md:10); output via `--format json --output <file>`; no offline switch | skillspector runs outside the sandbox only, and only with `scan.py --allow-osv` (it may send dependency names to OSV.dev); without it, coverage `blocked: needs network (OSV) — rerun with --allow-osv` |
| S7 | ✅ | gosec from the module root with `GOFLAGS=-mod=readonly GOPROXY=off GOTOOLCHAIN=local` → exit 0 on the clean Go file | as spec § 4.6 |
| S8 | ✅ | a subagent launched a nested subagent and got its reply | code-audit's lens 4 can run the full verifier panel; inline verification stays the fallback where dispatch is unavailable |

**Cache location**: `${SECSCAN_CACHE:-${XDG_CACHE_HOME:-$HOME/Library/Caches}/secscan}`.
On this machine `~/Library/Caches/secscan` is a symlink to
`/Volumes/NVMe2TB/shrix/Caches/secscan` (3.0 GB), keeping the system disk free.
