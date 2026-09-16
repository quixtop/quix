# SDLC matrix — phase → task key → tier, with rationale

Read this when classifying a prompt to task keys, or when a routing choice
needs justification. Tiers/efforts shown are shipped defaults —
references/config.md is authoritative at runtime. Traps list the
band-violation mistakes seen in practice, in both directions.

## Requirements & pre-design

| key | default | why |
|---|---|---|
| spec_clarification | top/high | Ambiguity resolution is judgment work |
| feasibility_analysis | top/high | Cross-cutting constraints, risk calls |
| epic_to_tickets | top/high | Decomposition quality gates everything after |

- Example: "turn this PRD into implementable tickets" → epic_to_tickets.
- Amplifiers: second_opinion on scope calls.
- Traps: routing ticket decomposition to mid (underkill — bad decomposition
  taxes every downstream task); frontier for a two-line clarifying question
  (overkill — no long horizon).

## Design

| key | default | why |
|---|---|---|
| architecture_bounded | top/xhigh | Known bounds — flagship judgment suffices |
| architecture_greenfield | frontier/high | Open-ended, long-horizon — frontier's lane |
| schema_design | top/xhigh | High blast radius, hard to reverse |
| second_opinion | top/high | Independent critique of a peer-tier decision |

- Example: "design a schema for multi-tenant billing" → schema_design.
- Amplifiers: second_opinion (near-mandatory here), tech_debt_notes.
- Traps: greenfield architecture on top (underkill — this is where the
  frontier lead is documented); bounded refactor-shaped design on frontier
  (overkill — bounds remove the differentiation).

## Implementation

| key | default | why |
|---|---|---|
| feature_well_scoped | mid/high | Parity zone — mid ≈ top on scoped work |
| feature_cross_file | top/high | Coupling needs flagship judgment |
| refactor_standard | mid/high | Pattern-following, well-understood |
| refactor_long_multifile | frontier/high | Frontier's biggest documented lead |
| boilerplate_scaffolding | light/low | Mechanical; volume lane |
| computer_use_automation | mid/high | Documented parity zone (see adapter) |

- Example: "add a --json flag to this CLI command" → feature_well_scoped.
- Amplifiers: diff_review, test_gap, lint_sweep; edge_case_hunt on logic.
- Traps: THE classic both ways. Short scoped feature on top = pure waste
  (quality-equivalence). "Simple-looking" feature that actually threads
  through five files on mid = underkill; check coupling before classifying.

## Debugging

| key | default | why |
|---|---|---|
| bugfix_known | mid/high | Cause known — implementation, not detection |
| debugging_hard_novel | top/xhigh | Novel failure modes need flagship reasoning |
| investigation_long_context | frontier/high | Huge-context dives — frontier floor |
| repro_bisect_logdive | mid/high | Systematic narrowing, not deep judgment |

- Example: "intermittent 502s only under load, no pattern in logs" →
  debugging_hard_novel.
- Amplifiers: test_gap (regression test), edge_case_hunt.
- Traps: hard novel bug on mid produces confident wrong diagnoses
  (underkill, expensive); a bisect script on top (overkill — the loop is
  mechanical).

## Testing

| key | default | why |
|---|---|---|
| unit_tests | mid/high | Well-scoped generation, near-top parity |
| test_gap_analysis | mid/high | Coverage reasoning, bounded scope |
| e2e_integration_design | mid/high | Scenario design within known system |
| edge_case_hunt | mid/high | Systematic enumeration |

- Amplifiers: lint_sweep on generated tests.
- Traps: unit tests on top (overkill — parity zone); test STRATEGY for a
  distributed system is architecture-shaped → escalate to top, don't leave
  on mid.

## Review

| key | default | why |
|---|---|---|
| diff_review_routine | mid/high | Convention + correctness scanning |
| diff_review_high_stakes | top/xhigh | Blast radius justifies flagship |
| security_review | top/xhigh | Pinned top — see active adapter's pin notes |

- Traps: security review NEVER goes to frontier even though it feels like
  "the hardest" work — the adapter documents why (predictability). Routine
  small-diff review on top burns the extras budget.

## Docs & comms

| key | default | why |
|---|---|---|
| docs_sync | light/low | Mechanical propagation of known changes |
| api_docs_judgment | mid/high | What-to-document requires code judgment |
| pr_description | light/low | Summarization of a known diff |
| commit_messages | light/low | Volume lane |
| release_notes | light/low | Template-following |

- Traps: docs that require deciding what matters (public API reference)
  on light = underkill; commit messages on mid = overkill, they're the
  canonical light task.

## Build, release, ops

| key | default | why |
|---|---|---|
| cicd_pipeline_config | mid/high | Config-shaped, well-documented domain |
| deployment_rollback_plan | top/xhigh | Irreversibility = blast radius |
| dependency_audit | light/low | Enumeration + lookup |
| dependency_migration | top/high | Cross-cutting breaking changes |

## Performance & data

| key | default | why |
|---|---|---|
| profiling_analysis | mid/high | Read numbers, spot hotspots |
| optimization_subtle | top/xhigh | Subtle correctness/perf tradeoffs |
| db_migration_backfill | top/xhigh | Data loss risk — highest blast radius |

## Maintenance

| key | default | why |
|---|---|---|
| issue_triage | light/low | Classification at volume |
| unfamiliar_codebase_dive | frontier/high | Huge-context comprehension — frontier floor |

## Composite prompts

Decompose, then route each key separately: "add feature X with tests and
docs" → feature_well_scoped + unit_tests + docs_sync — three lanes, three
tiers. Main-lane keys run interactive; amplifier-class keys run background.
No matching key → config's fallback_route, announced. Ambiguous → closest
key, stated so the user can correct it.
