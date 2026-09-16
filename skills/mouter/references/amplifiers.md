# Amplifier playbook — background quality extras

Each amplifier is toggleable in config.md (`amplifiers:` block) and
band-matched via its task key in the routing table. Queue enabled,
applicable extras as BACKGROUND runs after/alongside any substantive
main-lane task, within the fan-out cap.

## Universal rules

- Extras never block the main lane or the chat.
- Results come back as a concise digest: **checked / found / auto-fixed
  (mechanical only) / proposed** — non-mechanical changes are proposed
  diffs awaiting approval, never silently applied.
- Working tree only: NEVER commit, push, or stage.
- Never write the same file concurrently — serialize writes to shared
  targets (NOTES.md, README, changelog).
- One failure → rerun once on the next tier up; announce.
- Applicability: only queue extras that fit what the main lane just did
  (no security sweep on a docs edit; no docs sync when nothing user-facing
  changed).
- Redundancy: skip an extra when the main lane already IS that work — e.g.
  no security_sweep extra when the main task is a security_review, no
  test_gap extra when the main task is test_gap_analysis. State the skip
  in one line so the user sees it was considered, not forgotten.
- Tier resolution: every extra resolves through the routing table — run
  `scripts/resolve_model.py --task <key>` with the exact key named in its
  heading below. Extras without their own config key borrow the named
  proxy key; never guess and never fall through to fallback_route.

## The extras

### diff_review (config: diff_review; keys: diff_review_routine / diff_review_high_stakes)
- **Trigger**: any main-lane task that changed code.
- **Tier**: mid for routine; top when blast radius is high (auth, payments,
  data migration, public API).
- **Prompt template**: "Fresh-context review. You see ONLY this diff and
  these criteria — no author reasoning, by design. Diff: <diff>. Criteria:
  correctness, security, conventions, missing error handling at
  boundaries. Report findings ranked by severity with file:line."
- **Digest**: `review: N findings (X critical) — <one line each>`.

### test_gap (config: test_gap; key: test_gap_analysis)
- **Trigger**: code changed with test coverage plausibly affected.
- **Tier**: mid.
- **Prompt**: "Analyze <changed files> against existing tests. List
  uncovered behaviors introduced/changed by this diff, then write the
  missing tests as proposed files. Do not modify existing tests."
- **Digest**: `test-gap: N uncovered behaviors, M proposed tests`.

### edge_case_hunt (config: edge_case_hunt; key: edge_case_hunt)
- **Trigger**: new logic with inputs, state, or concurrency.
- **Tier**: mid; top if the failure modes are subtle (races, distributed
  state).
- **Prompt**: "Hunt edge cases and failure modes in <code>: nulls, empty
  collections, boundaries, races, error paths, resource exhaustion. For
  each: scenario → expected vs actual behavior."
- **Digest**: `edge-cases: N found (X confirmed reproducible)`.

### security_sweep (config: security_sweep; key: security_review)
- **Trigger**: changes touching auth, input handling, secrets, or network.
- **Tier**: top — respect the adapter's pin notes (never frontier where the
  adapter says so).
- **Prompt**: "Security sweep of <diff/files>: injection, authz/authn
  gaps, secret exposure, unsafe deserialization, SSRF, input validation at
  boundaries. Report per finding: severity, path, exploit sketch, fix."
- **Digest**: `security: N findings by severity`.

### docs_sync (config: docs_sync; key: docs_sync)
- **Trigger**: behavior or interface changed that docs describe.
- **Tier**: light.
- **Prompt**: "Update docs/changelog to match this diff: <diff>. Touch only
  statements the diff invalidates. Propose the edits."
- **Digest**: `docs: N files need sync, edits proposed`.

### lint_sweep (config: lint_sweep; resolve via --task boilerplate_scaffolding)
- **Trigger**: any code change; cheapest extra.
- **Tier**: light.
- **Prompt**: "Run the project's lint/type/static-analysis tools on
  <files>. Auto-fix mechanical findings in the working tree; list anything
  non-mechanical as proposed."
- **Digest**: `lint: N auto-fixed, M proposed`. (Auto-fix allowed: this one
  is mechanical by definition.)

### second_opinion (config: second_opinion; key: second_opinion)
- **Trigger**: high-stakes decisions — architecture, schema, irreversible
  choices.
- **Tier**: top.
- **Prompt**: "Independent critique of this decision: <decision +
  rationale>. Steelman it, then give the strongest counter-position and ONE
  concrete alternative with tradeoffs."
- **Digest**: `second-opinion: agrees/disagrees — <one-line stance +
  alternative>`.

### tech_debt_notes (config: tech_debt_notes; resolve via --task refactor_standard)
- **Trigger**: main-lane work exposed smells outside its scope.
- **Tier**: mid.
- **Prompt**: "Note refactor opportunities and tech debt observed in
  <files> to NOTES.md (append, serialized). Observations only — never apply."
- **Digest**: `tech-debt: N notes appended to NOTES.md`.
