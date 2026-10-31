# secscan — scoring and the report

## Severity anchors

| severity | anchor |
|---|---|
| critical | an unauthenticated attacker reads or changes others' data, runs code, or takes over accounts — at scale, now; a live production secret leaked |
| high | the same with a precondition an attacker can meet (a normal account, one click), or one tenant's data across tenants |
| medium | real harm that needs an unlikely precondition, or harm limited to the attacker's own scope with a security consequence |
| low | defence-in-depth gaps with a plausible but weak path |
| info | hardening notes — no shown attack |

Engine severities map to these (scan.py does it); the verifiers may lower an
engine finding after reading the code, and say why.

A committed secret is scored by exposure, since the scan never tests a key: high
when it is in the tree or history of a shared repo, critical once the owner says
it is live in production, lower only for a key marked fake
(`false-positives.md`).

## Tags

- `CWE-<n>` — the weakness, one primary.
- `OWASP:A<nn>` — OWASP Top 10:2025: A01 Broken Access Control · A02 Security
  Misconfiguration · A03 Software Supply Chain Failures · A04 Cryptographic
  Failures · A05 Injection · A06 Insecure Design · A07 Authentication Failures ·
  A08 Software or Data Integrity Failures · A09 Security Logging and Alerting
  Failures · A10 Mishandling of Exceptional Conditions.
- `LLM<nn>` (OWASP Top 10 for LLM Applications 2025) and `ASI<nn>` (Agentic
  Applications 2026) for AI and agent findings — LLM01 prompt injection, LLM05
  improper output handling, LLM06 excessive agency; ASI01 goal hijack, ASI02 tool
  misuse.

Common CWEs → OWASP 2025 (scan.py uses the same table): 89, 78, 79, 94, 77 → A05
· 22, 284, 285, 352, 639, 862, 863, 918 → A01 · 16, 611, 614, 942, 1004 → A02 ·
287, 306, 521, 522, 798 → A07 · 295, 319, 326, 327, 328, 330 → A04 · 1104, 1357,
1395 → A03 · 502, 829, 915 → A08 · 117, 532, 778 → A09 · 248, 703, 754, 755 → A10.

## Layout (in chat; the same in `--report` files)

1. Title line with mode, profile, revision (`sha12`, `-dirty`) and date; then
   the count of findings and coverage gaps (in chat, also findings by severity).
2. One table, most severe first: `# · severity · place · title · confidence · tags`.
3. Each finding below the table: evidence (code, never a value), the fix, its
   engines, the verifiers' verdict.
4. Needs validation — each with the fact the repo could not show.
5. Hardening notes.
6. Rejected candidates — a count, then one line each: place and reason. A
   wrongly rejected result must stay visible.
7. Called tools — one entry each: the tool and job (`claude-security` "Scan
   codebase", `security-audit`, …), where its report is, its findings by severity
   as it reported them (never re-scored; a `needs_validation` lead has none), or
   why it did not run, and its cost (agents, minutes, subagent tokens, else
   "cost not shown"). An ASVS 5.0 id secscan added to a `claude-security`
   finding is marked "added by secscan". The counts stay the tool's own; a
   finding an honoured precedent covers is listed under 8 and marked here as
   suppressed, so the two lists add up.
8. Suppressions honoured (allow markers, `.gitleaksignore`, `.semgrepignore`, and
   every `docs/security/precedents.md` entry applied, with its date and place).
9. Coverage — engines and their states, each top-level folder with what covered
   it, what was not covered and why (a tool not called counts), findings
   predating the change, engine versions, and the residual risk: a secret in a
   format no rule knows can reach a called tool unmasked.

Zero findings is a result: say it, with the coverage that backs it. With any
coverage gap it reads "no findings in what ran", never "clean".

## Report JSON

`scan.py report` takes the scan's own JSON with the verdicts filled in: the scan
document as printed by `--json` (`findings`, `groups`, `coverage`, `folders`,
`suppressions`, `revision`, `mode`, `versions`, `predates_change`), each
finding's `verdict`, `severity` and `confidence` as the verifiers set them (it
keeps its `id`), plus `profile`, `needs_validation` and `hardening` (lists of
strings), `rejected` (a list of `{"place", "reason"}`) and `tools` (a list of
`{"tool", "job", "report", "summary"}` — `summary` is the called tool's own
count line and its cost, or why it did not run).
