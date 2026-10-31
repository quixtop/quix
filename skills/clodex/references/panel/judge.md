# Judging a panel

The orchestrator judges by default — it is the only party that did not compete.
This is not a vote count and not a summary. It is a ruling on evidence.

## Order of operations

**1 · For code, RUN IT FIRST.** Before weighing any argument: execute the tests,
reproduce the bug, run the build. A proposal whose tests pass beats one that
merely reasons well, however elegantly. Execution is ground truth and it
outranks every rhetorical consideration below. Record what you ran and what it
printed — not "I verified it".

**2 · Sort every claim by what grounds it.**

| tier | grounding |
|---|---|
| executed | a command was run; its output is quoted |
| sourced | a file, line, citation, or measurement |
| reasoned | an argument from stated premises |
| asserted | confidence with nothing behind it |

Asserted claims lose to sourced ones regardless of how well written they are.
⚠️ Naive judging is sycophancy-prone: the most fluent, most confident answer
reads as the best one. Discount assertiveness deliberately — it is a style
signal, not an evidence signal.

**3 · Check what survived critique.** A claim attacked and defended is stronger
than one never examined. A claim attacked and abandoned is dead. A claim nobody
attacked is *untested*, not *validated* — mark it so.

**4 · Report the minority.** Never emit only the winner. A dissenting panellist
may hold the stronger argument while the others repeat one flawed line between
them. If a minority position had better grounding than the majority, say that
plainly — even when it did not win overall.

**5 · Treat agreement as weak evidence.** Models fail together; measured error
correlation across models is r=0.53–0.69. Three agreeing agents are not three
independent confirmations, and unanimity is not proof. When every panellist
agreed, say "all agreed, which is weaker evidence than it appears" rather than
presenting it as settled.

**6 · Be willing to return no verdict.** If the panel genuinely did not resolve
the question, say so and state precisely what would. A manufactured conclusion
is worse than an honest "unresolved" — it launders disagreement into false
confidence.

## Output shape

1. **Verdict** — the conclusion, and the evidence tier it rests on.
2. **Dissent** — every losing position, why it lost, and whether it deserved to.
3. **Evidence table** — claim · agent · grounding · survived critique.
4. **Untested claims** — asserted by someone, attacked by nobody.
5. **Configuration** — models, lenses, efforts, launch count.
   ⚠️ Report the RESOLVED model, never the alias typed. `cc:opus` is a moving
   pointer — it already shifted from Opus 4.8 once — so a verdict recording
   "opus" cannot be reproduced or compared later. Record `claude-opus-5`.
6. **Caveat, when the query was not code** — these methods are validated on
   reasoning benchmarks, not on design review. Say the finding is a strong prior
   rather than a measured result.
