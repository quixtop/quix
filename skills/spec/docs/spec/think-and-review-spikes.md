# think-and-review — spike notes
Status: approved 2026-10-28

Companion of `docs/spec/think-and-review.md` § 4.12. Written by plan Task 1;
Tasks 11–14 add their results below.

## Task 1 — can `claude -p` drive /spec headless?

**Verdict: `headless: yes`** (attempt 2, 2026-10-28, claude 2.1.311).

Run from a Terminal-panel tab, in a throwaway git repo under the session
scratchpad (one file, `app.py`), removed after:

```text
claude -p "/spec add a hello command" --output-format json --permission-mode acceptEdits --allowedTools "$allow"
claude -p --continue "recommended" --output-format json --permission-mode acceptEdits --allowedTools "$allow"
claude -p --continue "drop it" --output-format json --permission-mode acceptEdits --allowedTools "$allow"
allow='Read Glob Grep Agent Skill Write(docs/**) Edit(docs/**) Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(ls:*)'
```

| check | result |
|---|---|
| a question printed | ✅ turn 1 printed the vision block and the question batch (21 s) |
| `--continue` resumed the same session | ✅ every turn reported session `9bc8455b` |
| the spec file was written | ✅ `docs/spec/hello-command.md` and `docs/plan/hello-command.md` |
| a subagent ran | ✅ the spec's Review records an isolated reviewer round (0 C · 3 I · 9 M) |

Cost: $2.06 in all, ~4.5 min (turn 2: 237 s, 26 model turns).

**Attempt 1 failed**, and why matters for every later run: with
`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` set in this shell, `claude -p` forces the
permission mode back to default (its stderr says so), so `--permission-mode
acceptEdits` alone denied every write. Tools must be allowed explicitly with
`--allowedTools`; writes are limited to `docs/**` of the throwaway repo.

## Phase 5 dry runs (2026-10-28)

Each in a fresh fixture repo under the scratchpad, `claude -p` turn by turn
(`--allowedTools` as in Task 1, plus `Bash(git diff:*)`, `Bash(git ls-files:*)`
and the `checks.sh fp` command), removed after.

| task | check | result |
|---|---|---|
| 11 | drill: one question per turn, recommended answer, options | ✅ turn 1 |
| 11 | "recommended for the rest" ends the drill, gate still shows, plugin system kept | ✅ turn 2 |
| 11 | idea panel: 7 lenses + merger, one wave, top 5 routed | ⚠️ ran and routed (1 C · 14 I · 9 M; caught a real conflict: the rename spec would drop `tags`), but through the inline path below, not report files |
| 11 | panel names the plugin system as not needed | ⚠️ found, then set aside against Decided 1 — fixed in the /rev of 2026-10-28: such a problem now goes through § Contradictions |
| 11 | follow-up changed Decided → gate shown again | ✅ turn 4 |
| 11 | approach pick asks when approaches differ | ⚠️ not exercised: its approaches did not differ in scope, so it took A by rule; an owner override (B) then landed in Decided 4 and A in Alternatives with its reason |
| 11 | save point: `draft — concept`, Decided, Alternatives, ADR drafts, Review with cost line and every record | ✅ `idea panel: 8 agents · 420k tokens · 1.3 min`, all 24 problems kept |
| 11 | an extra "confirm" before the save point | ⚠️ not in the design — fixed in the /rev of 2026-10-28: think.md now lists the only turns that ask |
| 11 | resume in a fresh session: no drill question again, concept kept, review panel line added | ✅ Decided 4 (pick B), Alternatives and the idea-panel line kept; ⚠️ the line read `review panel (round 1): 6 agents (5 roles, 1 merger) · 410k tokens`, without minutes — not the fixed form; round 2 ran; $6.05, 5.8 min; `git status` showed only the two drafts |
| 12 | `/spec review seeded-spec.md`: missing rollback flagged | ✅ Critical #1; plan-only rows skipped and said; repo unchanged; ⚠️ inline path, and `review panel: 5 agents` left the merger out (the main run merged) |
| 12 | light mode: one batch, automatic pick, one reviewer, no panel | ✅ `single review: 1 agent · 63k tokens · 1 min`; fixes labelled `fixed — not re-reviewed` |
| 13 | `/spec verify`: `purge_old` undocumented, hard-coded path as drift, `save_note` nudge advisory, nothing changed | ✅ (the first run's fixture header named the seeds; re-run after the /rev with a clean header: ✅ again, $0.62 — ⚠️ it also flagged `save_note`/`list_notes` for missing docstrings though the README names them) |

**The inline path** (Tasks 11 and 12): under this `--allowedTools` list the
panel agents could not write scratchpad files, and `checks.sh fp` needed
approval. The runs improvised: reports returned in chat and merged by the
main run, `write check: not run — <why>` recorded, `git status` as a
substitute. No such fallback was designed then; the /rev of 2026-10-28 made
the inline report (taken by the merger) the design. The file-based path is
still unrun — owed in `docs/tasks.md`; that interactive sessions write the
scratchpad is unverified here.

**Task 1 caveat**: six Bash calls were denied in attempt 2 (the `git … :*`
patterns did not match the commands /spec ran); the run went on without them.
Phase 5 added `Bash(git diff:*)` and `Bash(git ls-files:*)`.

## Task 14 — owner checks

Each needs a failure made by hand, so the tests and dry runs cannot stage it.

| # | setup | expected result |
|---|---|---|
| 1 | `/spec` with a request too vague to state a goal ("make it better") | a panel agent returns `STOP: goal unclear`; the run shows what is missing and asks you, then reruns only the stopped agents |
| 2 | point a review role at a file it cannot read (a path under a folder the sandbox denies) | that role is `incomplete` in the merged file and in Review, never counted clean, with the path under `unread` |
| 3 | after the concept gate, answer something that contradicts a Decided entry | "This contradicts Decided <n>: which one stands?" and no file written that turn |
| 4 | `/rev` over a commit adding ~120 non-test lines in a repo with no spec naming them | the close carries `this range grew past a fix — spec it? /spec <topic>` |

Results are in § Proving runs, below.

## Proving runs (2026-10-28)

Five headless runs in parallel, each in a throwaway repo under the session
scratchpad, `claude -p --continue` turn by turn (claude 2.1.311), removed
after. Total $24.85 (estimate was $12–19), 34 min of turns.

| run | what | turns · min · $ |
|---|---|---|
| A | full `/spec` "sync notes between laptop and phone", file-based panels | 5 · 16.5 · 10.72 |
| B | Task 11 re-run: `/spec think` "add tags…; plugin system a must-have", inline path | 7 · 7.4 · 5.59 |
| C1 | `/spec review` on a spec with no stated goal | 2 · 4.0 · 3.65 |
| C2 | `/spec review` on a spec naming `vendor/storage.py`, reads of `vendor/**` denied | 1 · 2.6 · 3.18 |
| D | `/rev <base>` over a 132-line non-test commit, no spec | 1 · 3.5 · 1.71 |

| # | check | result |
|---|---|---|
| 1 | owner check 1: STOP | ✅ C1: 3 roles `STOP: goal unclear`, the gaps shown, asked; after the goal, only those 3 ran again with one new merger (`review panel: 4 agents · ~224k tokens · ~1.5 min`) |
| 2 | owner check 2: `incomplete` | ✅ C2: all 5 roles `incomplete` with `vendor/storage.py` unread, the claim reported unchecked, not false; 3 roles first called the file missing, the main run corrected it from `git ls-files` |
| 3 | owner check 3: contradiction | ✅ B turn 6: an approach-pick answer bringing back tag types → "This contradicts Decided 1 … Which one stands?", no file written that turn |
| 4 | owner check 4: /rev trigger | ✅ D: the close carried "the range grew past a fix … Spec it? `/spec tags`" (155 core lines) |
| 5 | you pick when approaches differ | ✅ A (one file per device vs one file per note) and B (inline vs index vs `#hashtags`) both asked; A named the part of Decided 1 the pick replaces |
| 6 | file-based panel path | ✅ A: 7 lens files + merged, then 5 role files + merged; C1 turn 2: 3 role files + merged; every write check matched before and after |
| 7 | Task 11: only the listed turns ask | ✅ B: drill, gate, gate again after a correction, 1 follow-up, approach pick, contradiction; the save point wrote in the same turn as the answer |
| 8 | Task 11: inline path, merger | ✅ B: the 7 lens reports came back inline and the merger took them; ⚠️ C1 turn 1 and C2: the main run merged inline reports itself (fixed, F2) |
| 9 | save point | ✅ B: `draft — concept`, Decided (with the pick), Alternatives with reasons, 2 ADR drafts, `idea panel: 8 agents · 456k tokens · 2.5 min`, write check |
| 10 | full flow to the go | ✅ A: spec with companions inside it, phased plan, review panel 0 C / 20 I fixed, `review panel: 6 agents · ~449k tokens · ~2.9 min`; "drop it" filed nothing |

**Findings**

| # | finding | fix |
|---|---|---|
| F1 | `<scratchpad>` had no meaning in a session without one: A wrote its panel files to `/tmp/panel-state` (the `/clodex --panel` state folder), C1 to the parent session's scratchpad | `references/review.md` § Agent tools: fall back to `$TMPDIR/spec-panels/`, never a folder another tool keeps; test-pinned |
| F2 | standalone review skipped the merger when every report came back inline (C1 turn 1, C2; Task 12 too) | § Merger: the merger always runs, the main conversation never merges; test-pinned |
| F3 | B's concept gate labelled every Assumption "becomes Decided when you confirm"; `think.md` § Concept gate makes only request- or code-found ones Decided. The run corrected itself at the save point | `think.md` § Concept gate: the Assumptions shown in two labelled groups; test-pinned |

**For the next headless run**: allow scratchpad writes with `Edit(//<path>/**)`
— Claude Code checks a Write against Edit rules, so `Write(//…)` alone denies
it. A correction at the concept gate or a follow-up answer replaces Decided by
design; only an approach-pick answer or a panel problem can raise
§ Contradictions.

## Model A/B (2026-10-30)

`/tune` for cost: three headless runs on the toy fixture, the candidate
installed as a project skill. Costs are from each run's `total_cost_usd` and
`modelUsage`.

| run | panel model | cost | findings | seeded problem |
|---|---|---|---|---|
| `/spec review seeded-spec.md` | session (Opus) | $3.05 · `review panel: 6 agents · ~330k tokens` | 1 C · 11 I · 2 M | missing rollback: Critical and Important |
| same, candidate | review roles on `sonnet` | $2.35 (sonnet $0.77) · ~335k tokens | 0 C · 7 I · 2 M | caught, but only as Important |
| `/spec think` "add tags…; plugin system a must-have" | lenses on `sonnet` | panel turn $2.34 (sonnet $1.11) | 3 C · 13 I · 8 M | plugin contract challenged through § Contradictions |

Kept: the idea lenses on `sonnet` (the seeded problem caught, the counts no
worse than run B's 1 C · 14 I · 9 M). Rejected: the review roles on `sonnet`
(a Critical missed). One sample each; `sonnet` panel agents cost about 1.9×
less than the session model's, estimated from the first two rows.
