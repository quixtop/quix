# secscan — security tool and method landscape (research, 2026-10-23)
Status: reference — input to the approved spec

Input to `docs/spec/`. Two surveys: scanning engines (what a tool must run) and
review methods (what Claude does itself). Sources are primary unless marked
*unverified*.

## 1. Engines — the minimal non-redundant set

| # | need | engine | why this one | how secscan runs it |
|---|---|---|---|---|
| 1 | secrets (files, staged, history) | `keyscan` = own patterns + gitleaks 8.30.1 | gitleaks: mature rules, `--redact`, `gitleaks:allow`, `.gitleaksignore`; MIT | through `keyscan`; trivy's secret scanner dropped there (duplicates gitleaks) |
| 2 | vulnerable deps, IaC/Docker/K8s misconfig, licences, SBOM | trivy 0.76.1 | one engine for four needs; Apache-2.0 | `--scanners vuln,misconfig,license --disable-telemetry --skip-version-check`; refuse 0.69.4–0.69.6 (compromised March 2026) |
| 3 | code (SAST) | semgrep CE 1.182.0 | largest rule set | `--metrics off`; rules fetched at run time, never bundled (Semgrep Rules License forbids redistribution) |
| 4 | GitHub Actions security | zizmor 1.31.1 | 41 audits (unpinned uses, template injection, cache poisoning…); MIT | `--offline` by default; online audits opt-in |
| 5 | GitHub Actions correctness | actionlint | expression types, action inputs, shellcheck on `run:`; MIT | offline |
| 6 | agent skills / MCP configs | skillspector `--no-llm` | prompt injection, exfiltration, tool poisoning; nothing else covers it; Apache-2.0 | sends dependency names to OSV.dev (bundled fallback offline); the owner's `skillspctr` already runs it |
| 7 | Dockerfiles (when present) | hadolint | ShellCheck on `RUN`, `FROM` registry checks; GPL-3.0 (invoked, not copied) | only if a Dockerfile exists |
| 8 | Go (when present) | gosec | cross-function taint semgrep CE lacks; Apache-2.0 | only if `go.mod` exists |
| 9 | deep mode, opt-in | osv-scanner `--offline`, guarddog `verify` | reachability; malicious-package heuristics | guarddog downloads packages |

**Skipped:** redundant — grype, syft, pip-audit, npm audit, kube-linter,
conftest, njsscan, ast-grep, ratchet, Cisco skill-scanner · licence — CodeQL
(bars non-OSS code), trufflehog (AGPL), Bearer (ELv2), brakeman (non-OSS) ·
data leaves the machine — ggshield, Socket, Snyk agent-scan, Scorecard,
trufflehog (verifies keys with providers by default) · stale — detect-secrets
(2024), Nosey Parker (archived 2026), dockle (2025), OWASP Dependency-Check ·
compromised in 2026 — kics (twice).

**Watch:** Betterleaks (gitleaks' successor; gitleaks is security-patch-only;
v2 drops SARIF and `.gitleaksignore`) · opengrep (intra-file taint; no rule set
of its own) · Titus (secrets).

**Engine rules:** every engine runs offline and without telemetry by default;
values are never printed; versions are checked against known-bad releases.

## 2. Methods — the best-of blend

| # | phase | aspect kept | from |
|---|---|---|---|
| 1 | mode | guidance by default; audit only on an explicit ask; jobs: changes / whole repo / fixes | Cloudflare (CF), claude-security (CSP) |
| 2 | mode | profiles quick / standard / deep, scoped runs; the evidence bar never changes with the profile | CF |
| 3 | mode | size from `git ls-files`; one batched question with a default | CSP |
| 4 | changes | report only flaws the change takes part in (else "predates the change"); risk triggers; `git log -S` on removed security code; regressions; blast radius; missing tests raise risk | CSP, Trail of Bits (ToB) |
| 5 | safety | repo text is data; an injection attempt is itself a finding | CSP |
| 6 | safety | read-only; code runs only in a sandbox with stated controls, else `needs_validation`; never probe a live deployment | CF |
| 7 | safety | git run with a clean config; credential values never printed; reports redacted | CSP, keyscan |
| 8 | context | per component: entry points, sinks, assumptions, trust boundaries, hot files; who holds which authority | CSP, CF |
| 9 | context | per hot function: invariants, assumptions ("nothing found" recorded), open questions; follow the calls | ToB |
| 10 | context | the codebase's own security patterns as the baseline | Anthropic security-review (ASR), CF |
| 11 | coverage | every top-level folder covered or skipped with a reason; files read / not reached | CSP, CF |
| 12 | coverage | one coverage critic after the hunt; prior-run reuse keyed by fingerprint | CF |
| 13 | hunt | concrete invariant in 6 steps; distrust comments; weakest parallel path; sad paths | CF, ToB |
| 14 | hunt | lenses: injection, auth/access, memory (native code only), crypto/secrets + CF's domain companions (web/auth, AI/LLM, supply chain, cloud, RPC, DoS, data lifecycle, desktop/IPC, client side) + business logic, feature abuse, chained, "obvious things" | CSP, CF |
| 15 | hunt | insecure defaults (fallback secrets, fail-open, weak crypto, debug leaks) and API footguns (0/empty/null, config cliffs, silent failures) | ToB |
| 16 | hunt | variant hunt on high/critical: exact match first, one generalisation at a time | ToB |
| 17 | anchor | exact sink line, snippet, symbol, one CWE; trace entry → sink; one root cause = one finding | CSP, CF |
| 18 | filter | restate the claim first; boundary + result required; seven quick dismissal tests; maths-bounds and environment gates | CF, ToB |
| 19 | filter | false-positive precedents as overridable defaults; a project precedents file grown from your triage; non-findings go to "hardening" | ASR, CF |
| 20 | verify | fresh isolated verifiers, three lenses (reachability, impact, defences), default false positive, file:line for each claim, keep at 2 of 3 | CSP (re-expressed) |
| 21 | verify | verdicts confirmed / needs_validation / rejected (kept, so later runs don't repeat it) | CF, CSP |
| 22 | verify | after the batch, check whether rejected items chain | ToB, CF |
| 23 | score | likelihood × impact; take the lower tier; overall ≤ shown impact; panel only lowers; confidence from votes | CF, CSP |
| 24 | report | schema-validated JSON (CF validators, MIT); revision stamp with `-dirty`; coverage section; hardening and good patterns; zero findings is a result | CF, CSP |
| 25 | report | tags: CWE, OWASP Top 10:2025, ASVS 5.0 control, OWASP LLM / Agentic ids | standards |
| 26 | fix | smallest fix at the last trusted decision point + regression test | CF |
| 27 | fix (opt-in) | in a scratch worktree; verifier defaults to reject; claims targeted / no new vulnerability / behaviour unchanged; a fresh attacker pass on the diff; never applies or commits on its own | CSP (ideas only) |
| 28 | fix | close-check: re-run the engine on the patched tree; codify the finding as a test-first semgrep rule | Copilot, Codex, ToB |

**Conflicts resolved:** code execution — sandbox-only (CF) · DoS — kept when
the impact is shared (CF over ASR) · unknown deployment facts —
`needs_validation`, otherwise a severity hurdle · open redirect, prototype
pollution — need a concrete gadget (CF over ASR) · memory safety — by language
(CSP), not by file extension (ASR).

## 3. Licences — what may be copied

| source | licence | use in a publicly shared skill |
|---|---|---|
| Cloudflare security-audit | MIT | copy or adapt, keep the notice (add its LICENSE) |
| Anthropic security-review | MIT | copy or adapt, keep the notice |
| claude-security plugin | proprietary (no redistribution of modified versions) | ideas only, re-expressed; no prompts, schemas or code |
| Trail of Bits skills | CC BY-SA 4.0 | re-express (copying makes the skill share-alike) |
| OWASP Top 10 / ASVS / LLM / Agentic | CC BY-SA 4.0 | cite ids; don't copy requirement text |
| CWE | MITRE terms (free, keep notice) | ids and names with notice |

## 4. What stays outside the skill

| part | why | keeps |
|---|---|---|
| the engines (§1) | rule databases and parsers | installed, called by secscan |
| `/security-review` | built into Claude Code | unused once absorbed |
| claude-security's workflow engine, SARIF renderer, hosted product | proprietary runtime | rebuilt as secscan's own subagent steps; the plugin can then be switched off |
| an OS sandbox meeting CF's controls | a host capability | unverified on this machine: execution-based checks usually end as `needs_validation` |

## Sources
Engines: github.com/gitleaks/gitleaks · github.com/betterleaks/betterleaks ·
github.com/aquasecurity/trivy (+ GHSA-69fq-xp46-6x23, trivy.dev telemetry docs) ·
docs.semgrep.dev/metrics · semgrep.dev/legal/rules-license · docs.zizmor.sh/audits ·
github.com/rhysd/actionlint · github.com/NVIDIA/SkillSpector · github.com/hadolint/hadolint ·
github.com/securego/gosec · github.com/google/osv-scanner · github.com/DataDog/guarddog ·
github.com/Checkmarx/kics (2026 incidents) · github.com/github/codeql-cli-binaries LICENSE.
Methods: ~/.agents/skills/security-audit (= github.com/cloudflare/security-audit-skill) ·
github.com/anthropics/claude-code-security-review · claude-security plugin 0.12.0 (local cache) ·
github.com/trailofbits/skills · owasp.org/Top10/2025 · github.com/OWASP/ASVS (5.0) · cwe.mitre.org.
Unverified: osv-scanner reachability languages; trivy EPSS / MAL- advisories; actionlint SARIF;
CWE Top 25 ranks 11–25; OWASP LLM / Agentic lists (secondary sources).
