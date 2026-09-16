# Round 2 — adversarial critique framing

Used by: Claude (mentally, output in conversation) and Codex (passed verbatim
as task prompt). The skill substitutes `{{QUERY}}` and `{{OTHER_AI_ANSWER}}`
before sending to Codex.

**Bias control:** the critic must NOT be told who wrote the answer being
critiqued. Always frame as "another AI proposed this" so neither model is
deferential or dismissive based on brand identity.

---

You are critiquing another AI's proposed answer to a request. Do this in two
clearly separated passes:

## 1. Steelman first (1–2 short paragraphs)

State the strongest, most charitable interpretation of the other AI's answer.
What's the best version of what they're saying? What real problem does their
approach solve? Be honest — if their answer is good, say so before attacking.

## 2. Attack second (the bulk of your response)

Identify, with specifics:

- **The weakest assumption.** What did they take for granted that's actually
  contestable? Cite the assumption explicitly.
- **The biggest gap.** What important consideration did they miss entirely?
- **The likely failure mode.** Under what real-world condition does their
  approach break, scale poorly, or produce a bad outcome?
- **At least one specific technical disagreement.** Name the line, decision,
  library, or pattern you think is wrong, and explain why with a concrete
  alternative consideration (without yet proposing your own full answer).

## Hard constraint

**Do NOT propose your own alternative answer in this round.** Critique only.
The synthesis stage handles which side wins each disagreement.

---

ORIGINAL REQUEST:
{{QUERY}}

ANOTHER AI'S ANSWER (to critique):
{{OTHER_AI_ANSWER}}

YOUR CRITIQUE (steelman first, then attack):
