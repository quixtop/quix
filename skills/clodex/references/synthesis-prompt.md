# Round 3 — synthesis framing

Used by: Claude only (Codex does not get a synthesis turn).

You now have the following artifacts in your context:

- **(A)** Your own round-1 proposal (in conversation, earlier this session)
- **(B)** Codex's round-1 proposal (`$STATE_DIR/r1-codex.md`)
- **(C)** Your critique rounds 2 through M — `r2` and (for N ≥ 4) any
  re-critique rounds `r3`..`r{M}` you wrote. All in conversation; the latest
  may also be on disk as `$STATE_DIR/r{M}-claude.md` if Step 2.6a persisted
  it for the revision input.
- **(D)** Codex's critique rounds 2 through M — `$STATE_DIR/r2-codex.md` and
  (for N ≥ 4) `$STATE_DIR/r3-codex.md` … `$STATE_DIR/r{M}-codex.md`.
- **(E)** *If Step 2.6 self-revision ran:* Your revised round-1
  (`$STATE_DIR/r1-claude-revised.md`)
- **(F)** *If Step 2.6 self-revision ran:* Codex's revised round-1
  (`$STATE_DIR/r1-codex-revised.md`)

Where `M` = the last critique round that actually ran (N-1 in the normal case,
or earlier if the convergence guard fired in Step 2.5). For the default N=3
case, M=2 — so (C) and (D) are exactly the r2 critiques.

**Which artifacts to judge between (the critical revision-mode distinction):**

- If (E) and (F) exist on disk → judge between the REVISED R1s. (A)/(B)/(C)/(D)
  are *context* for understanding what was contested, NOT the artifacts being
  judged. The revisions absorbed the landed critique points already, so synthesis
  is choosing between refined positions.
- If (E) and (F) are absent (`--no-revise` mode or revision failed) → judge
  between the original first-draft (A)/(B) using (C)/(D) as the critique
  context. Legacy behaviour.

Produce ONE final settled answer to the original request. Apply these rules:

## Rule 1 — Lock in agreements

Where (A) and (B) substantively agree, that's settled. Don't manufacture
conflict where none exists. Briefly mention the agreement to the user (one
sentence) so they know it's deliberate, not glossed-over.

## Rule 2 — Judge disagreements on technical merit

For each contested point, read **all critique rounds — (C) and (D) in full,
including any re-critique rounds for N ≥ 4** — and ask: *which side's critique
landed?* Which side's argument is stronger on the technical merits? Points
raised in later re-critique rounds count equally with points raised in r2.

**Critical:** do NOT default to your own round-1 position. Assess as a
third-party reviewer would. If Codex's critique of you is sharper than yours
of Codex, Codex wins that point.

## Rule 3 — Annotate decisions inline

For each major decision in the final answer, append ONE short bracketed line
citing which side's argument prevailed. Format examples:

```
[r1: claude wins — codex's critique relied on assumption Y, which doesn't apply here]
[r1: codex wins — claude's r1 missed the concurrent-access case codex raised]
[agreed: both r1s converged on this approach]
```

Keep these terse. They're audit notes, not essays.

## Rule 4 — End with a decision log

After the final answer, add a brief **Decision Log** section: 3 to 5 of the
most consequential contested points, each as one sentence. Format:

```
## Decision Log
- <Contested point>: <winner> — <one-line why>
- <Contested point>: <winner> — <one-line why>
- ...
```

## Rule 5 — Tone and structure

The final answer should be **confident, specific, with code or concrete
references where helpful**. The user gets ONE answer, not a discussion of how
you got there. The decision log handles the meta-narrative.

Skip throat-clearing intros. Don't recap the question or restate that you ran
a dialectic. Begin with the answer itself.

---

ORIGINAL REQUEST:
{{QUERY}}

Begin the final settled answer now.
