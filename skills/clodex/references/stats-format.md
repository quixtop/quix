# Stats block format rules

Used by: SKILL.md Step 3d. Lazy-loaded only when synthesizing the final answer.

The Stats block is mandatory on every clodex run — never skip it. It's the user's
signal for both (a) whether the protocol added marginal value on this question
(Attribution row) and (b) what it cost to compute (Time taken row).

## Exact format

```
═══ STATS ═══
  Attribution: Claude (<claude_pct>%)  |  Codex (<codex_pct>%)  |  Agreed (<common_pct>%)
  Time taken:  Claude (<claude_total>s)    |  Codex (<codex_total>s)
```

## Format rules

- **Header**: exactly `═══ STATS ═══` (all-caps, matching `FINAL SETTLED ANSWER`).
- **Body**: two lines, each indented with TWO leading spaces.
- **Labels**:
  - `Attribution:` followed by ONE trailing space before `Claude`.
  - `Time taken:` followed by TWO trailing spaces before `Claude` (compensates
    for the shorter label width so `Claude` aligns vertically).
- **Inter-metric separator**: `  |  ` (two-space pipe two-space) on the
  Attribution row.
- **Inter-metric separator on Time taken row**: `    |  ` (four-space pipe
  two-space) — the extra two leading spaces compensate for `(12s)` being
  shorter than `(42.9%)`, keeping the `Codex` column vertically aligned.
- **Order on Attribution**: `Claude` → `Codex` → `Agreed`. Claude first
  (runs locally), Codex second, Agreed last (baseline).
- **Order on Time taken**: `Claude` → `Codex`. Agreed has no separate time.
- **Values**: in parentheses. `(42.9%)` for percentages (one decimal place);
  `(12s)` for seconds (integer, no decimals).
- **No trailing semicolons** anywhere on either line.
- **No "rule of thumb"** or interpretation text appended to the block — the
  numbers speak for themselves.

## Render rules for the DIALECTIC COMPLETE header line

```
═══ clodex DIALECTIC COMPLETE (<actual_rounds> rounds<revise_note><convergence_note>) ═══
```

- `<actual_rounds>` = the round number where synthesis happened (3 in default
  case; 2–5 if user requested non-default rounds or convergence aborted early).
- `<revise_note>` = ` + revise` when Step 2.6 self-revision ran successfully
  (`$STATE_DIR/r1-codex-revised.md` exists); empty when `--no-revise` was set or
  revision failed and synthesis fell back to original R1s.
- `<convergence_note>` = empty when run completed normally, OR
  ` — early-converged from N=<requested_N>` if the convergence guard fired.
- List one `R<k>: codex resume <uuid>` line for every Codex round actually run.
- If revision ran, also list `Revise: codex resume <uuid>` line for the
  revision job (extract session-id from `r1-codex-revised.md`).

## Width caveat

The 4-space-vs-2-space alignment trick works perfectly when timings are 1–3
digit seconds (`Claude (12s)` etc). For very long runs (`Claude (543s)` or
longer), the visual `Codex` alignment breaks slightly. Functional but cosmetic.
If this becomes a problem, switch to dynamic spacing computed at render time.
