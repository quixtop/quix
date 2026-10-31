# Job catalogue

A job is a **role** — what an agent does and which phases it joins. A lens is a
**method** — how it thinks. They are independent and compose freely:
`@verify=reason-backwards` is coherent and useful.

Editable. Add jobs that suit your work; each must declare its phases.

---

## (default) — all phases
Proposes in phase 1, critiques in phase 2. The right choice for almost every
agent, and the only one that works at N=2.

## @propose — phase 1
Answers, then falls silent. Use when you want a voice in the room but not
another critic — an agent with a strong prior worth capturing, without letting
it also grade the others.

## @critique — phase 2
Attacks without proposing. Never anchored to a position of its own, so it has
nothing to defend. Costs half a normal agent and adds pure adversarial pressure.

⚠️ A panel of only `@critique` agents has nothing to critique. At least one
agent must reach phase 1.

## @verify — phase 2, executes
Does not argue. Takes the claims made in phase 1 and checks them: runs the test,
reproduces the bug, reads the file, confirms the citation. Reports what happened,
not what should happen.

⚠️ **`cc` agents only.** Codex cannot execute — measured: `sandbox-exec:
Operation not permitted`. A codex `@verify` produces reasoning wearing the label
of verification, which is worse than no verifier at all.

## @research — phase 1
Gathers prior art rather than opinion: what already solved this shape of
problem, what it learned, where the analogy stops. Contributes evidence for
others to argue over instead of a position to defend.

## @judge — phase 3
Takes judging from the orchestrator. Use when you want a specific model ruling
rather than the orchestrator.

⚠️ The orchestrator is the only party that did not compete. A delegated judge
grades peers it sat out of only by assignment — a weaker guarantee of
neutrality, not no guarantee. Worth it when you specifically want another
model's judgement; not worth it by default.

---

## Defining your own

    @<name>:<phases>     phases ∈ 1, 2, 3 — comma-separated for several

    --job devils-advocate:2="Argue the panel is asking the wrong question
      entirely. Name the question it should be asking instead."

Rules:
1. **A job must join at least one phase.** Zero phases is an error, not a no-op.
2. **Say what to DO, not who to BE.** "Argue the question is wrong" is a job;
   "you are the contrarian" is a costume, and the same fixed-mental-set finding
   that governs lenses applies here.
3. **Executing jobs must be `cc`.** Any job whose text says run, test, or
   reproduce inherits the codex limitation above.
4. Custom jobs are per-invocation. Add one here to make it permanent.
