# Self-revision framing (Step 2.6, default on)

Used by: Claude (mentally, output written to `$STATE_DIR/r1-claude-revised.md`) and
Codex (passed verbatim as task prompt, result captured to
`$STATE_DIR/r1-codex-revised.md`).

The skill substitutes `{{QUERY}}`, `{{YOUR_ORIGINAL_ANSWER}}`, and
`{{CRITIQUE_OF_YOU}}` before sending to Codex.

**When this is used:** by default on every clodex run, between Step 2 (cross-
critique) and Step 3 (synthesis). Skipped when the user invoked with `--no-revise`.

**Bias control:** the critique is framed as "another AI critiqued your earlier
answer" without naming Claude or Codex, matching the convention used in Round 2.

---

Another AI critiqued the answer you wrote earlier. Read the critique carefully,
then produce a *revised version of your answer* — same scope as your original,
but improved where the critique landed.

For each critique point, either:

- **Incorporate it silently** — fold the improvement into the revised answer
  without flagging the change. This is what should happen for most landed
  critiques.
- **Push back briefly** — if you disagree with a critique, include one short
  line in the revised answer noting why you're keeping your original position.

## Hard constraints

- The output is a **revised version of your answer**, not a debate response
  or point-by-point rebuttal. The reader should see a cleaner answer, not a
  conversation about the critique.
- Same scope and approximate length as your original. Don't bloat — sharpen.
- Don't reference "the critique" in the body of the revised answer unless
  you're explicitly pushing back on a point.

---

ORIGINAL REQUEST:
{{QUERY}}

YOUR ORIGINAL ANSWER:
{{YOUR_ORIGINAL_ANSWER}}

ANOTHER AI'S CRITIQUE OF YOUR ANSWER:
{{CRITIQUE_OF_YOU}}

YOUR REVISED ANSWER (same scope, sharpened by the critique you accept):
