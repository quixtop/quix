# dep — concurrency, in full
<!-- author: shrix -->

READ before step 1 of a dep with more than one target, surface, suite or review
slice. `dep/SKILL.md` § Concurrency keeps the summary.

⚠️ The review split below is for reviews dep dispatches itself. `/rev`
writes fixes, so it runs ONCE over the changed set no earlier review covers —
never one per target in parallel, which would have several loops editing the
same tree.

## Concurrency (the default, not an optimization to remember)
A `dep` is mostly *waiting* — on suites, on bundlers, on propagation, on
subagents. Independent waits run TOGETHER; serial is the exception and needs a
stated reason. Cost scales with targets × surfaces, so batching is what keeps
a large repo tractable and a small one instant.
- **Reviews** — N independent slices ⇒ **N agents in ONE message**, never one
  agent asked to walk them in turn. A single agent reads slice 2 only after
  finishing slice 1, so its wall-clock is the SUM where N agents' is the MAX.
  The review is typically the LONGEST step in a dep — measured at ~⅓ of one —
  which makes splitting it the single biggest lever on how long a dep takes.
  Split by what can be judged independently: per target, per slice, per concern.
  Same when one review would otherwise cover several targets.
- **Suites** — independent suites (separate runners/dirs) run in one wave. A
  project script that walks them serially is worth fixing *at the script*,
  not working around here.
- **Probes** — every target × surface in ONE round; a convergence poll
  re-probes the whole set each round. Never walk surfaces one at a time.
- **Ship actions** — parallel where the toolchain is proven safe; serial where
  it is not. Before defaulting to serial, check whether the hazard has a known
  REMOVAL. The classic trap is a shared package-manager cache lock: concurrent
  invocations race it and the losers abort — but invoking the locally-installed
  binary directly does no package resolution at all, which eliminates the race
  rather than tiptoeing around it. Serial-by-reflex on a fleet of deployables is
  a long, avoidable wait.
  ⚠️ Even with the hazard gone, batch MODESTLY (3–4 at a time), not N-wide:
  provider APIs throttle or bot-challenge a burst, and one rejected ship costs
  far more than the seconds a wider fan-out would have saved.
- **Never parallelize ACROSS a gate.** review+tests → refactor → ship →
  verify stay strictly ordered. Concurrency lives *inside* a step, never
  through one.
