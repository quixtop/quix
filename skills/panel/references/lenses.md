# Lens catalogue

A lens is a **reasoning method** — how the agent thinks. It is never a persona.
DMAD's finding: a role label over unchanged reasoning still produces a fixed
mental set, so "you are the security reviewer" buys nothing. "Start from the
failure and work backwards" changes the search order, and that is what diverges.

Editable. Add methods that suit your work; keep them methods.

---

## reason-backwards
Begin at the failure. Assume this is already broken in production — describe
how, then work back to what in the proposal permits it. Do not start from the
design and look for flaws; start from the flaw and look for its cause.

## first-principles
Discard the framing. What must be true regardless of how anyone has solved this
before? Rebuild from those constraints and see whether you arrive anywhere near
the proposal. Where you diverge is the finding.

## cheapest-sufficient
Find the smallest thing that actually satisfies the requirement. Treat every
component as guilty until proven load-bearing. If a simpler construction meets
the stated need, the difference is unjustified complexity — name it.

## attack-assumptions
Identify the single belief the proposal rests on most heavily and try hardest to
break. If it holds, say so plainly. If it does not, everything above it falls,
so state what falls with it.

## steelman-opposite
Take the alternative the proposal rejected — or never considered — and argue it
at full strength, as its best advocate would. Only then compare. A rejected
option argued weakly was never really compared.

## analogy-prior-art
What existing system has this exact shape? What did it get right, and what did
it learn the hard way? Reason from that precedent rather than from scratch, and
name where the analogy stops holding.

## execution-first
*(code tasks)* Do not argue about whether it works. Run it. Write the failing
case, execute it, report what happened. A claim you have not executed is a
hypothesis, and should be labelled one.

---

## Assignment rules

1. **Spend diversity where model diversity is lowest.** Three agents of one
   model have only their lenses to differentiate them — give those maximally
   distinct methods. A lone agent of its own model already contributes
   heterogeneity, so its lens matters less.
2. **Never assign by model affinity.** No evidence supports "Codex is better at
   correctness" or similar. Assigning that way is superstition with a design
   justification bolted on.
3. **Prefer `execution-first` for at least one agent on code tasks.** The coding
   literature is execution-grounded: tests passing outranks argument quality,
   so at least one agent should be checking rather than reasoning.
4. **Do not repeat a lens within a panel** unless every method is already used.
