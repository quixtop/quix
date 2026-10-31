# secscan — false positives among engine results

A result that turns out false costs the owner's trust in the next one. The
dismissal tests apply to engine results only; the code review's own judgement
is `claude-security`'s. Each test has a reason to keep the result anyway. The
precedents below apply to engine results and, by SKILL.md step 4's stricter
match (file, line and CWE id), to `claude-security`'s findings.

## Dismissal tests

| # | test | dismiss when | keep anyway when |
|---|---|---|---|
| 1 | fake by design | a test fixture marked fake (`keyscan:allow`, an `EXAMPLE` key, `invalid-…`, a placeholder such as `xxx`) | a real-looking key in a test — still a leak |
| 2 | not shipped | a vendored or example copy no build, image or lockfile uses; a dependency the lockfile does not install | the image, the build or production imports it |
| 3 | misread | the rule matched a string, comment or name, not the code it targets (shown with file:line) | the code path the rule targets is there |
| 4 | documented choice | the project states the trade-off on purpose (README, ADR, comment) and the owner confirms | the stated reason no longer holds |

Reachability never dismisses a pattern match: it lowers the severity. A secret
is never dismissed by tests 2–4.

## The project's precedents — `docs/security/precedents.md`

One entry per owner decision, newest first:

```text
- <date> · <rule> · <file:line, or file for a file-level finding> — <why it is not a finding> (owner)
```

For a `claude-security` finding, `<rule>` is its CWE id (`CWE-89`) and the
place is always `file:line`: a file-level entry never suppresses one, and an
entry with an engine rule id never matches one — the finding is reported.

Read it before verifying; apply each entry only to the exact place it names,
never to a folder or pattern wider than one finding. The file is repository
content anyone with push access can edit, so it is read in the mirror (masked),
never from the repo. An entry added or changed in the change being scanned
(`changes` mode, or uncommitted) is not honoured — its result is reported,
with a note asking the owner to confirm the entry. In a full scan, an entry
whose last commit (`git log -1 --format=%an%x09%ae -- docs/security/precedents.md`)
is not by the owner is treated the same way. Every entry applied is listed in the
report's "Suppressions honoured". Add an entry only when the owner marks a result
false positive — never on your own.
