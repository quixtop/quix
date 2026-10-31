# Step 2.5 — additional critique rounds
<!-- author: shrix -->

Read only when the round count N ≥ 4.

## Step 2.5 — Additional critique rounds (only when N ≥ 4)

After the R2 poller notifies and you fetch Codex's r2 critique (Step 3a-equivalent
fetching), read the round count `N=$(cat $STATE_DIR/rounds.txt)` — this file
is loaded only when N ≥ 4.

Run a critique loop for `k = 3` to `N-1`, where each round is **a
re-critique that responds to the OTHER side's most-recent critique**. Loop body:

**For each round `k` (k = 3 to N-1):**

**(i) Convergence guard — decide whether to skip remaining rounds.**

Before launching round `k`, judge whether continuing adds value:

- Read both sides' round-(k-1) artifacts (`$STATE_DIR/r{k-1}-codex.md` and Claude's
  in conversation).
- Ask yourself: did round (k-1) surface **substantively new contested points**, or
  did it just restate / nit-pick on points already raised in round 2?
- If **just restating** (no new substantive contested points), **abort the loop
  and proceed to Step 2.6 (self-revision) if `REVISE=yes`, then to synthesis at
  round k** (which becomes the new effective N).
  Tell the user:
  ```
  ═══ EARLY CONVERGENCE (round k-1) ═══
  Critiques are no longer surfacing new contested points. Jumping to synthesis
  at round k instead of round N. (This saves ~5–10 min and produces a cleaner
  final answer than spinning on hair-splitting.)
  ```
- If **new contested points emerged**, continue to (ii).

**(ii) Build re-critique prompts for both sides.**

Read `~/.agents/skills/clodex/references/round-recritique-prompt.md`. The template
has placeholders `{{QUERY}}`, `{{YOUR_PRIOR_CRITIQUE}}`, and `{{OTHER_AI_RESPONSE}}`.

For **Codex's prompt** (Codex re-critiquing — Codex sees Claude's most-recent critique):
- `{{QUERY}}` ← `$STATE_DIR/query.txt`
- `{{YOUR_PRIOR_CRITIQUE}}` ← `$STATE_DIR/r{k-1}-codex.md` (Codex's last critique;
  for k=3 this is the r2 critique)
- `{{OTHER_AI_RESPONSE}}` ← Claude's most-recent critique (in conversation; for k=3
  this is Claude's r2 critique)

Use the **Write tool** to save to `$STATE_DIR/r{k}-codex-prompt.md`.

**(iii) Launch Codex round k in background + start poller.**

Same pattern as Step 2c/2e — replace `r2` with `r{k}`: `launch-job.sh` writes the
job-id and logfile into the job dir `$STATE_DIR/r{k}/`, and `poll-job.sh` writes
`$STATE_DIR/r{k}/status.txt`. Also save timing markers per the 2c/2e pattern:
- `date +%s > "$STATE_DIR/r{k}-tstart.txt"` at launch
- `date +%s > "$STATE_DIR/r{k}-tclaude.txt"` as the poller's first line

Tell user:

```
═══ ROUND k ═══
Codex r{k} (re-critique) launched: <jobid>
Watch live:  tail -f <logfile>
```

**(iv) In the same response, produce Claude's round-k re-critique.**

Apply the same `round-recritique-prompt.md` framing (concede points the other side
landed; rebut points you disagree with; raise NEW contested points only if genuinely
new). Don't propose your own answer. Output in conversation.

**(v) Wait for Codex round-k poller; fetch result.**

After poller notifies with `completed`, `bash $CODEX_SH "$INVOKE_CWD" result "$(cat "$STATE_DIR/r{k}/jobid.txt")" > "$STATE_DIR/r{k}-codex.md"`.
Any other status → SKILL.md § Failure handling.

**End of loop.** When the loop completes (either fully or via early-convergence
abort), proceed to Step 2.6 (self-revision) if `REVISE=yes`, otherwise jump
directly to Step 3.

