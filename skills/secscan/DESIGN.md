# secscan — design

## Report
- Title line: mode, profile, revision, date. Then the count of findings and coverage gaps, with "Zero findings — see coverage below" when nothing was found and nothing was missed, or "No findings in what ran — the gaps below were not checked" when a gap exists.
- Repeated findings (one row per rule repeating inside one skill or file, with its finding numbers); one findings table by severity (# · severity · place · title · confidence · tags); each finding's claim, evidence, sources and fix below.
- Then needs-validation, hardening notes, rejected candidates (a count, then place and reason each), called tools (each tool and job, its report's path, its own counts or why it did not run), suppressions honoured (applied precedents included), and coverage: engines and states, top-level folders, engine versions, findings predating the change, the residual risk.
- While engines run, one stderr line per engine (`▸ <engine> <state> at N s`, plus `, N raw hit(s)` when it ran); keyscan's names the places to revoke first.
