# Re-critique framing (rounds 3+)

Used by: Claude (mentally, output in conversation) and Codex (passed verbatim
as task prompt). The skill substitutes `{{QUERY}}`, `{{YOUR_PRIOR_CRITIQUE}}`,
and `{{OTHER_AI_RESPONSE}}` before sending to Codex.

**When this is used:** only when the user invoked clodex with `--rounds N` where
`N ≥ 4`. For the default 3-round protocol, this template is never read — round 2
uses `round2-prompt.md` and round 3 is synthesis.

**Bias control:** the critic still must NOT be told who wrote the answers. Frame as
"another AI". The skill ensures the OTHER side's response is passed verbatim, with
no brand identification.

---

You previously critiqued another AI's answer to a request. The other AI also
critiqued YOUR previous critique (or your earlier proposal). Now respond to their
critique. Apply this structure:

## 1. Concede (1 short paragraph)

Identify the points where the other AI's critique of you was correct. Don't be
defensive — if a critique landed, say so explicitly. This is the most important
part: it's how the dialectic actually converges instead of rotating.

## 2. Rebut (1–2 short paragraphs)

For points where you disagree with the other AI's critique, rebut with specifics:

- **Why their critique misses the mark.** Cite the assumption in their critique
  that doesn't hold, or the context they're missing.
- **What stands from your prior position.** Restate the part of your earlier
  critique you're keeping, with sharper reasoning.

## 3. New ground (only if genuinely new — otherwise omit this section)

If the back-and-forth has surfaced a genuinely new contested point that hasn't been
discussed yet (in any prior round), name it with a one-line setup. **Be honest:** if
nothing new emerged, write *"No new contested points this round."* This signal is
what the skill uses to detect convergence and exit early.

## Hard constraint

Still no full alternative answer. Concede + rebut + (optional) new ground only.
The synthesis stage handles which side wins each contested point.

---

ORIGINAL REQUEST:
{{QUERY}}

YOUR PRIOR CRITIQUE (what you said last round):
{{YOUR_PRIOR_CRITIQUE}}

ANOTHER AI'S RESPONSE TO YOUR CRITIQUE (what to respond to now):
{{OTHER_AI_RESPONSE}}

YOUR RE-CRITIQUE (concede first, then rebut, then optional new ground):
